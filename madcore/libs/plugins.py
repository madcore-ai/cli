from __future__ import unicode_literals, print_function

import logging

from madcore.base import PluginsBase
from madcore.libs.cloudformation import StackManagement

logger = logging.getLogger(__name__)


class PluginManagement(PluginsBase, StackManagement):
    def execute_plugin_jenkins_job(self, plugin_name, job_name, parsed_args):
        job_type = 'jobs'
        job_params = self.get_plugin_job_final_params(plugin_name, job_name, job_type, parsed_args)

        jenkins_params = self.params_to_jenkins_format(job_params)

        jenkins_job_name = self.get_plugin_jenkins_job_name(plugin_name, job_name)

        job_success = self.jenkins_run_job_show_output(jenkins_job_name, parameters=jenkins_params)

        if job_success:
            self.save_plugin_jobs_params_to_config(plugin_name, job_name, job_type, job_params, parsed_args)

        self.update_core_params(jenkins_params, job_name)

        return job_success

    def execute_plugin_create_cloudformation_job(self, plugin_name, job_name, parsed_args):
        job_type = 'cloudformations'
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']
        stack_details = self.get_stack(stack_name, debug=False)

        if not stack_details or self.is_stack_create_failed(stack_details):
            job_params = self.get_plugin_job_final_params(plugin_name, job_name, job_type, parsed_args)

            stack_template_body = self.get_plugin_template_file(plugin_name, job_definition['template_file'])
            dict_job_params = self.plugin_params_to_dict(job_params)

            stack_details, exists, updated = self.create_stack_if_not_exists(
                stack_name,
                stack_template_body,
                dict_job_params,
                capabilities=job_definition['capabilities']
            )

            self.save_plugin_jobs_params_to_config(plugin_name, job_name, job_type, job_params, parsed_args)
        else:
            self.logger.info("[%s] Stack already created with status: '%s'.", stack_name, stack_details['StackStatus'])

        self.update_core_params(self.stack_output_to_dict(stack_details), job_name)

        return True

    def execute_plugin_delete_cloudformation_job(self, plugin_name, job_name, parsed_args):
        job_type = 'cloudformations'
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']

        stack_deleted = self.delete_stack_if_exists(stack_name)

        return stack_deleted

    def execute_plugin_status_cloudformation_job(self, plugin_name, job_name, parsed_args):
        job_type = 'cloudformations'
        job_definition = self.get_plugin_job_definition(plugin_name, job_name, job_type=job_type)

        stack_name = job_definition['stack_name']

        stack_details = self.get_stack(stack_name)

        if stack_details:
            self.logger.info("Stack create with status: '%s'.", stack_details['StackStatus'])

        return stack_details

    def execute_plugin_job(self, plugin_name, job_name, parsed_args):
        job_definition = self.get_plugin_job_definition(plugin_name, job_name)

        CF_ACTIONS = {
            'create': self.execute_plugin_create_cloudformation_job,
            'delete': self.execute_plugin_delete_cloudformation_job,
            'status': self.execute_plugin_status_cloudformation_job,
        }

        if 'sequence' in job_definition:
            _results = []
            for sequence in job_definition['sequence']:
                self.logger.info("Execute %s sequence '%s'.", sequence['type'], sequence['name'])
                self.logger.info(sequence['description'])

                if sequence['type'] in ('job',):
                    jenkins_job_result = self.execute_plugin_jenkins_job(plugin_name, sequence['job_name'], parsed_args)
                    _results.append(jenkins_job_result)
                elif sequence['type'] in ('cloudformation',):
                    executor = CF_ACTIONS.get(sequence['action'], None)

                    if callable(executor):
                        cf_result = executor(plugin_name, sequence['job_name'], parsed_args)
                    else:
                        self.logger.error("Invalid sequence action: %s", sequence['action'])
                        self.exit()
                        # TODO@geo maybe execute here status or other commands?
                        cf_result = None

                    _results.append(cf_result)

            success = all(_results)
        else:
            success = self.execute_plugin_jenkins_job(plugin_name, job_name, parsed_args)

        return success
