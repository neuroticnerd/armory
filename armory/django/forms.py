from __future__ import absolute_import, unicode_literals
from __future__ import division, print_function

import uuid

from datetime import datetime
from django import forms
from crispy_forms import layout, helper, bootstrap
from crispy_forms.utils import TEMPLATE_PACK


class RangeWidget(forms.widgets.MultiWidget):
    """ django widget for displaying values representing a range """

    def __init__(self, widgets_from=None, widgets_to=None, **kwargs):
        """ `widgets_from` and `widgets_to` should be instantiated widgets """
        attrs_from = kwargs.pop('attrs_from', {})
        attrs_to = kwargs.pop('attrs_to', {})
        widget_class = kwargs.pop('widget_class', None)
        if widget_class is None and widgets_from is None:
            raise ValueError('either widget_class or widgets_from is required')
        if widget_class is None and widgets_to is None:
            raise ValueError('either widget_class or widgets_to is required')
        if widgets_from is None:
            widgets_from = [widget_class(attrs=attrs_from)]
        if widgets_to is None:
            widgets_to = [widget_class(attrs=attrs_to)]
        range_widgets = []
        try:
            iter(widgets_from)
        except TypeError:
            widgets_from = [widgets_from]
        try:
            iter(widgets_to)
        except TypeError:
            widgets_to = [widgets_to]
        range_widgets.extend(widgets_from)
        range_widgets.extend(widgets_to)
        self._from_to_divisor = len(widgets_from)
        super(RangeWidget, self).__init__(widgets=range_widgets, **kwargs)

    def decompress(self, value):
        if isinstance(value, (list, tuple)):
            return value
        if value is None:
            return []
        return (value, value)

    def format_output(self, rendered_widgets):
        lower = rendered_widgets[:self._from_to_divisor]
        upper = rendered_widgets[self._from_to_divisor:]
        return str().join([self.addon_from] + lower + [self.addon_to] + upper)

    def build_input_addon(self, content=None, elem=None, classes=None):
        css_class = 'input-group-addon'
        addon = '<{elem} class="{classes}">{content}</{elem}>'
        content = content if content is not None else ''
        elem = elem if elem is not None else 'span'
        if classes is None:
            addon_classes = css_class
        else:
            addon_classes = ' '.join([css_class, classes])
        return addon.format(elem=elem, classes=addon_classes, content=content)

    @property
    def addon_from(self):
        if not hasattr(self, '_addon_from'):
            self._addon_from = self.build_input_addon('from')
        return self._addon_from

    @property
    def addon_to(self):
        if not hasattr(self, '_addon_to'):
            self._addon_to = self.build_input_addon('to')
        return self._addon_to


class RangeField(forms.fields.MultiValueField):
    """ django form field for displaying two values representing a range """

    def __init__(self, field_class, widget_class=None, *args, **kwargs):
        self.field_class = field_class
        self.widget_class = widget_class
        init_from = kwargs.pop('init_from', {})
        attrs_from = init_from.pop('attrs', {})
        init_to = kwargs.pop('init_to', {})
        attrs_to = init_to.pop('attrs', {})
        if widget_class:
            init_from['widget'] = widget_class(attrs=attrs_from)
            init_to['widget'] = widget_class(attrs=attrs_to)
        field_from = field_class(**init_from)
        field_to = field_class(**init_to)
        if not widget_class:
            field_from.widget.attrs.update(attrs_from)
            field_to.widget.attrs.update(attrs_to)
        if isinstance(field_from.widget, forms.MultiWidget):
            widgets_from = field_from.widget.widgets
        else:
            widgets_from = field_from.widget
        if isinstance(field_to.widget, forms.MultiWidget):
            widgets_to = field_to.widget.widgets
        else:
            widgets_to = field_to.widget
        range_widget = RangeWidget(widgets_from, widgets_to)
        kwargs['initial'] = (
            init_from.get('initial', None),
            init_to.get('initial', None),
        )
        super(RangeField, self).__init__(
            fields=(field_from, field_to),
            widget=range_widget,
            *args, **kwargs
        )

    def compress(self, data_list):
        if data_list:
            lower = self.fields[0].clean(data_list[0])
            upper = self.fields[1].clean(data_list[1])
            return (lower, upper)
        return tuple()


class IntegerRangeField(RangeField):
    def __init__(self, *args, **kwargs):
        super(IntegerRangeField, self).__init__(
            field_class=forms.fields.IntegerField,
            widget_class=forms.widgets.NumberInput,
            *args, **kwargs
        )


class DateTimeRangeWidget(RangeWidget):
    """ django widget for displaying datetime values representing a range """

    def format_output(self, rendered_widgets):
        lower = rendered_widgets[:self._from_to_divisor]
        upper = rendered_widgets[self._from_to_divisor:]
        if len(lower) > 1:
            lower.insert(1, self.addon_date)
            lower.append(self.addon_time)
        else:
            lower.append(self.addon_datetime)
        if len(upper) > 1:
            upper.insert(1, self.addon_date)
            upper.append(self.addon_time)
        else:
            upper.append(self.addon_datetime)
        return str().join([self.addon_from] + lower + [self.addon_to] + upper)

    @property
    def addon_date(self):
        if not hasattr(self, '_addon_date'):
            date_classes = 'glyphicon glyphicon-date'
            self._addon_date = self.build_input_addon(classes=date_classes)
        return self._addon_date

    @property
    def addon_time(self):
        if not hasattr(self, '_addon_time'):
            time_classes = 'glyphicon glyphicon-time'
            self._addon_time = self.build_input_addon(classes=time_classes)
        return self._addon_time

    @property
    def addon_datetime(self):
        if not hasattr(self, '_addon_datetime'):
            dt_classes = 'glyphicon glyphicon-datetime'
            self._addon_datetime = self.build_input_addon(classes=dt_classes)
        return self._addon_datetime


class DateTimeRangeField(RangeField):
    widget = DateTimeRangeWidget

    def __init__(self, split=False, *args, **kwargs):
        self._split = split
        if split:
            field_class = forms.SplitDateTimeField
            widget_class = forms.SplitDateTimeWidget
        else:
            field_class = forms.DateTimeField
            widget_class = forms.DateTimeInput
        super(DateTimeRangeField, self).__init__(
            field_class=field_class,
            widget_class=widget_class,
            *args, **kwargs
        )

    def compress(self, data_list):
        if data_list:
            return [datetime.Date(v) for v in data_list]
        return None


class CrispyField(layout.Field):
    """ crispy_forms Field overrides """
    def __init__(self, *args, **kwargs):
        if 'label_class' in kwargs:
            self.label_class = kwargs.pop('label_class')
        if 'field_class' in kwargs:
            self.field_class = kwargs.pop('field_class')
        super(CrispyField, self).__init__(*args, **kwargs)

    def render(
            self, form, form_style, context,
            template_pack=TEMPLATE_PACK, extra_context=None, **kwargs):
        if extra_context is None:
            extra_context = {}
        if hasattr(self, 'label_class'):
            extra_context['label_class'] = self.label_class
        if hasattr(self, 'field_class'):
            extra_context['field_class'] = self.field_class
        return super(CrispyField, self).render(
            form, form_style, context, template_pack, extra_context, **kwargs
        )


class CrispyMultiWidgetField(CrispyField):
    def __init__(self, *args, **kwargs):
        if 'wrapper_class' in kwargs:
            self.wrapper_class = kwargs.pop('wrapper_class')
        if 'label_class' in kwargs:
            self.label_class = kwargs.pop('label_class')
        if 'field_class' in kwargs:
            self.field_class = kwargs.pop('field_class')
        self.fields = list(args)
        self.attrs = kwargs.pop('attrs', {})
        self.template = kwargs.pop('template', self.template)


class PanelFormHelper(helper.FormHelper):
    """helper specifically for creating bootstrap 3 forms within Panels"""
    PANELTYPES = ('default', 'primary', 'success', 'info', 'warning', 'danger')

    def __init__(self, title, panel=None, **options):
        super(PanelFormHelper, self).__init__()
        self._layout = None
        self._form_collapse = options.get('collapse', False)
        self.form_method = options.get('method', 'POST')
        if panel is None:
            panel = 'default'
        if panel not in self.PANELTYPES:
            errmsg = '{0} is not a valid bootstrap panel: valid panels are {1}'
            raise ValueError(errmsg.format(panel, self.PANELTYPES))
        self._panel_class = '{0} panel-{1}'.format('panel', panel)
        self._panel_title = None
        if title is not None:
            h1_title = '<h1 class="panel-title">{0}</h1>'
            self._panel_title = h1_title.format(title)
        self.form_class = 'form form-horizontal'
        self.label_class = 'col-lg-2 col-md-2 col-xs-2'
        self.field_class = 'col-lg-8 col-md-9 col-xs-10'
        form = options.get('form', None)
        self._form = form
        form_layout = options.get('layout', None)
        if form_layout is not None:
            self.layout = form_layout
        elif form is not None:
            form_actions = options.get('form_actions', [])
            self.layout = self.default_bootstrap_layout(form, form_actions)

    def default_bootstrap_layout(self, form, actions=None):
        actions = [] if actions is None else actions
        form_fields = []
        small_fields = (
            forms.ChoiceField, forms.IntegerField, forms.DateTimeField
        )
        for name, field in form.fields.items():
            attrs = {}
            if isinstance(field, small_fields):
                attrs['field_class'] = 'col-lg-2 col-md-3 col-xs-4'
            if isinstance(field.widget, forms.widgets.MultiWidget):
                form_fields.append(
                    CrispyMultiWidgetField(name, wrapper_class='multifield')
                )
            else:
                form_fields.append(CrispyField(name, **attrs))
        form_layout = layout.Layout(*form_fields)
        form_actions = []
        for action in actions:
            if action['type'] == 'submit':
                args = {}
                if 'class' in action:
                    args['css_class'] = 'btn-{0}'.format(action['class'])
                form_actions.append(layout.Submit(
                    action['name'],
                    action['value'],
                    **args
                ))
            if action['type'] == 'reset':
                args = {}
                if 'class' in action:
                    args['css_class'] = 'btn-{0}'.format(action['class'])
                form_actions.append(layout.Reset(
                    action['name'],
                    action['value'],
                    **args
                ))
        if not actions:
            form_actions.append(layout.Submit('submit', 'Submit'))
        form_layout.append(bootstrap.FormActions(*form_actions))
        return form_layout

    @property
    def layout(self):
        return self._layout

    @layout.setter
    def layout(self, value):
        self._layout = value
        panel_id = getattr(self, 'form_panel_id', None)
        panel_id = uuid.uuid4().hex if panel_id is None else panel_id
        collapse = ' in' if self._form_collapse else ''
        self.all().wrap_together(
            layout.Div,
            css_class='panel-body{0}'.format(collapse),
            id='{0}'.format(panel_id)
        )
        collapse_options = {}
        if self._form_collapse:
            collapse_options['data_toggle'] = 'collapse'
            collapse_options['data_target'] = '#{0}'.format(panel_id)
            collapse_options['aria_expanded'] = 'true'
        if self._panel_title is not None:
            self._layout.insert(0, layout.Div(
                layout.HTML(self._panel_title),
                css_class='panel-heading',
                **collapse_options
            ))
        self.all().wrap_together(layout.Div, css_class=self._panel_class)


class BootstrapPanelForm(forms.Form):
    """
    Base for bootstrap panel forms which use django-crispy-forms

    Attributes you can set on inherited class:
        ``form_title``: sets the bootstrap panel heading (supports jinja2)
        ``form_context``: sets the bootstrap context coloring for the panel
        ``form_method``: sets the form method (defaults to 'post')
        ``form_id``: sets the DOM id for the form
        ``form_collapse``: whether the form is collapsible (default: False)
        ``form_panel_id``: sets the DOM id for the panel body of the form
    """

    @property
    def helper(self):
        if not hasattr(self, '_helper'):
            self._helper = self.form_setup()
        return self._helper

    def form_setup(self):
        pfh_options = {
            'title': getattr(self, 'form_title', ''),
            'panel': getattr(self, 'form_context', 'default'),
            'method': getattr(self, 'form_method', 'post'),
            'collapse': getattr(self, 'form_collapse', False),
            'form': self,
        }
        if hasattr(self, 'form_actions'):
            pfh_options['form_actions'] = self.form_actions
        pfh = PanelFormHelper(**pfh_options)
        if hasattr(self, 'form_id'):
            pfh.form_id = self.form_id
        if hasattr(self, 'form_panel_id'):
            pfh.form_panel_id = self.form_panel_id
        return pfh
