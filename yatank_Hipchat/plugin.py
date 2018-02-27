# -*- coding: utf-8 -*-

import os
import re
import importlib
from jinja2 import Environment, FileSystemLoader, Template
from yandextank.plugins.Aggregator import \
    AggregatorPlugin, AggregateResultListener
from yandextank.core import AbstractPlugin
from hc import HipChatBot


class HipchatPlugin(AbstractPlugin, AggregateResultListener):

    '''Hipchat report plugin '''
    SECTION = 'hipchat'
    STAGES = ['prepare_test', 'start_test',
              'end_test', 'post_process']

    @staticmethod
    def get_key():
        return __file__

    def __init__(self, core):
        AbstractPlugin.__init__(self, core)
        self.log.info("yatank_Hipchat init ...")
        self.options = {'server': ('', True),
                        'token': ('', True),
                        'rooms': ([], False),
                        'users': ([], False),
                        'domain': ('', True)}
        self.hipchat = None
        self.collector = None
        self.end_time = None
        self.data_plugin = None

    def _configure_hipchat(self):
        options_valid = True
        options = {}
        for name in self.options:
            value = self.options[name][0]
            value_type = type(value)
            if value_type is str:
                value = self.get_option(name, value)
            elif value_type is list:
                value = re.split("[,; ]+", self.get_option(name, value))
            options[name] = value
        for name in options:
            require = self.options[name][1]
            if not options[name] and require:
                if name == 'domain' and (not options['users']):
                    continue
                options_valid = False
                self.log.warning("Hipchat: '%s' option is required" % name)
            self.options[name] = options[name]
        if options_valid:
            try:
                self.log.info("Hipchat Options: %s" % self.options)
                self.hipchat = HipChatBot(self.options)
            except Exception, exc:
                self.log.warning("Hipchat Configure Issue: %s" % exc)

    def get_available_options(self):
        ini_options = self.options.keys()
        ini_options += ['templates_dir_path']
        base_names = ['message_template', 'message_template_file_name']
        for bn in base_names:
            ini_options += ["%s_%s" % (bn, stage)
                            for stage in HipchatPlugin.STAGES]
        return ini_options

    def configure(self):
        self.templates_dir_path = self.get_option('templates_dir_path', '')
        try:
            data_plugin_module = self.get_option('data_plugin_module')
            data_plugin_class = self.get_option('data_plugin_class')
            m = importlib.import_module(data_plugin_module)
            c = getattr(m, data_plugin_class)
            self.data_plugin = self.core.get_plugin_of_type(c)
        except Exception, exc:
            self.log.warning("No plugin providing data: %s" % exc)
        self._configure_hipchat()

    def prepare_test(self):
        self.notify('prepare_test')

    def start_test(self):
        self.notify('start_test')

    def end_test(self, retcode):
        self.notify('end_test')
        return retcode

    def post_process(self, retcode):
        self.notify('post_process')
        return retcode

    def render_template_value(self, base_name, stage, interim_data):
        opt_name = "%s_%s" % (base_name, stage)
        template_value = self.get_option(opt_name, '')
        if not template_value:
            return ''

        t = Template(template_value)
        return t.render(interim_data)

    def render_template_message(self, base_name, stage, interim_data):
        value = self.render_template_value(base_name, stage, interim_data)
        if value:
            return value
        if not self.templates_dir_path:
            return ''

        opt_name = "%s_%s_%s" % (base_name, 'file_name', stage)
        file_name = self.get_option(opt_name,
                                    'hipchat_%s_%s' % (base_name, stage))
        file_path = os.path.join(self.templates_dir_path, file_name)
        if not os.path.exists(file_path):
            self.log.info("Template %s file is not exist." \
                          % file_path)
            return ''
        env = Environment(loader=FileSystemLoader(self.templates_dir_path))
        template = env.get_template(file_name)
        return template.render(interim_data)

    def notify(self, stage):
        if not self.hipchat:
            self.log.warning("Stage: %s. Hipchat Bot is not created." \
                             % stage)
            return
        if not self.data_plugin:
            self.log.warning("Stage: %s. Data plugin is not provided." \
                             % stage)
            return
        interim_data = self.data_plugin.get_data(stage)
        message = self.render_template_message('message_template', stage,
                                               interim_data)
        if not message:
            return
        format = interim_data.get('hipchat_message_format', 'text')
        color = interim_data.get('hipchat_message_color', 'gray')
        try:
            self.hipchat.msg_to_rooms(message, format, color)
        except Exception, exc:
            self.log.warning("Hipchat Notify Issue: %s" % exc)
        try:
            self.hipchat.msg_to_users(message)
        except Exception, exc:
            self.log.warning("Hipchat Notify Issue: %s" % exc)
