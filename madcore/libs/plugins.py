from __future__ import unicode_literals, print_function

import logging

from madcore import const
from madcore.base import JenkinsBase
from madcore.libs.cloudformation import StackManagement

logger = logging.getLogger(__name__)


class PluginManagement(JenkinsBase, StackManagement):
    def execute_plugin_jenkins_job(self, plugin_name, job_name, parsed_args, job_params=None):
        job_type = const.PLUGIN_JENKINS_JOB_TYPE

        if not job_params:
            job_params = self.get_plugin_job_final_params(plugin_name, job_name, job_type, parsed_args)

        jenkins_params = self.params_to_jenkins_format(job_params)

        jenkins_job_name = self.get_plugin_jenkins_job_name(plugin_name, job_name)

        job_success = self.jenkins_run_job_show_output(jenkins_job_name, parameters=jenkins_params)

        if job_success:
            self.save_plugin_jobs_params_to_config(plugin_name, job_name, job_type, job_params, parsed_args)

        return job_success

    def execute_plugin_create_cloudformation_job(self, plugin_name, sequence, parsed_args):
        job_name = sequence['job_name']
        job_type = const.PLUGIN_CLOUDFORMATION_JOB_TYPE
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']
        stack_details = self.get_stack(stack_name, debug=False)

        if not stack_details or self.is_stack_create_failed(stack_details):
            job_params = self.get_plugin_job_final_params(plugin_name, job_name, job_type, parsed_args)

            stack_template_body = self.get_plugin_template_file(plugin_name, job_definition['template_file'])
            dict_job_params = self.list_params_to_dict(job_params)

            stack_details, exists, updated = self.create_stack_if_not_exists(
                stack_name,
                stack_template_body,
                dict_job_params,
                capabilities=job_definition['capabilities']
            )

            if (not exists or updated) and self.is_stack_create_complete(stack_details):
                try:
                    asg_name = self.get_output_from_dict(stack_details['Outputs'], 'AutoScalingGroupName')
                    self.wait_for_auto_scale_group_to_finish(asg_name)
                except KeyError:
                    pass

            self.save_plugin_jobs_params_to_config(plugin_name, job_name, job_type, job_params, parsed_args)
        else:
            self.logger.info("[%s] Stack already created with status: '%s'.", stack_name, stack_details['StackStatus'])

        self.update_core_params(self.stack_output_to_dict(stack_details), job_name, add_madcore_prefix=False)

        return True

    def execute_plugin_update_cloudformation_job(self, plugin_name, sequence, parsed_args):
        job_name = sequence['job_name']
        job_type = const.PLUGIN_CLOUDFORMATION_JOB_TYPE
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']
        stack_details = self.get_stack(stack_name, debug=False)

        if not stack_details:
            self.logger.error("Cluster not created.")
            self.exit()
        elif self.is_stack_create_failed(stack_details):
            self.logger.error("Cluster created by failed.")
            self.exit()

        self.update_core_params(self.stack_output_to_dict(stack_details), job_name, add_madcore_prefix=False)

        sequence_params = []

        # TODO@geo we need to fix this and make sure we get from configs parameters
        # ask for sequence parameters
        if sequence.get('parameters', None):
            sequence_params = self.load_plugin_job_validators(sequence['parameters'])
            sequence_params = self.ask_for_plugin_parameters(sequence_params, parsed_args)

        stack_template_body = self.get_plugin_template_file(plugin_name, job_definition['template_file'])

        updated = self.update_stack_if_changed(
            stack_name,
            stack_template_body,
            stack_details,
            self.list_params_to_dict(sequence_params),
            capabilities=job_definition['capabilities']
        )

        stack_details = self.get_stack(stack_name, debug=False)

        if updated and self.is_stack_update_complete(stack_details):
            try:
                asg_name = self.get_output_from_dict(stack_details['Outputs'], 'AutoScalingGroupName')
                self.wait_for_auto_scale_group_to_finish(asg_name)
            except KeyError:
                pass

        self.save_plugin_jobs_params_to_config(plugin_name, job_name, job_type, sequence_params, parsed_args)

        return updated

    def execute_plugin_delete_cloudformation_job(self, plugin_name, sequence, parsed_args):
        job_name = sequence['job_name']
        job_type = const.PLUGIN_CLOUDFORMATION_JOB_TYPE
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']

        self.delete_stack_if_exists(stack_name)

        # does's matter if stack already deleted, we still consider it as deleted
        return True

    def execute_plugin_status_cloudformation_job(self, plugin_name, sequence, parsed_args):
        job_name = sequence['job_name']
        job_type = const.PLUGIN_CLOUDFORMATION_JOB_TYPE
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']

        stack_details = self.get_stack(stack_name)

        if stack_details:
            self.logger.info("Stack create with status: '%s'.", stack_details['StackStatus'])

            self.update_core_params(self.stack_output_to_dict(stack_details), job_name, add_madcore_prefix=False)

        return stack_details

    def execute_plugin_job(self, plugin_name, current_job_name, parsed_args):
        job_definition = self.get_plugin_job_definition(plugin_name, current_job_name)

        CF_ACTIONS = {
            'create': self.execute_plugin_create_cloudformation_job,
            'update': self.execute_plugin_update_cloudformation_job,
            'delete': self.execute_plugin_delete_cloudformation_job,
            'status': self.execute_plugin_status_cloudformation_job,
        }

        # first of all check if current job does have parameters
        job_parameters = self.get_plugin_job_final_params(plugin_name, current_job_name, const.PLUGIN_JENKINS_JOB_TYPE,
                                                          parsed_args)
        if job_parameters:
            # make the input params available for alter use like
            # <JOB_NAME>_<PARAM_NAME>
            self.update_core_params(self.list_params_to_dict(job_parameters), current_job_name,
                                    add_madcore_prefix=False, param_to_upper=True)

        if 'sequence' in job_definition:
            _results = []
            for sequence in job_definition['sequence']:
                self.logger.info("Execute %s sequence '%s'.", sequence['type'], sequence['name'])
                self.logger.info(sequence['description'])

                if sequence['type'] in ('job',):
                    # don't send the parameters because it's different job
                    if sequence['job_name'] != current_job_name:
                        job_parameters = None

                    jenkins_job_result = self.execute_plugin_jenkins_job(plugin_name, sequence['job_name'], parsed_args,
                                                                         job_parameters)
                    _results.append(jenkins_job_result)
                elif sequence['type'] in ('cloudformation',):
                    executor = CF_ACTIONS.get(sequence['action'], None)

                    if callable(executor):
                        cf_result = executor(plugin_name, sequence, parsed_args)
                    else:
                        self.logger.error("Invalid sequence action: %s", sequence['action'])
                        self.exit()
                        # TODO@geo maybe execute here status or other commands?
                        cf_result = None

                    _results.append(cf_result)

            success = all(_results)
        else:
            success = self.execute_plugin_jenkins_job(plugin_name, current_job_name, parsed_args, job_parameters)

        return success
