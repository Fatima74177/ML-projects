from django import forms

from .models import Attendance


class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        exclude = ['created_at']
        widgets = {
            'attendance_date': forms.DateInput(
                attrs={'type': 'date', 'class': 'form-control'},
                format='%Y-%m-%d',
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['attendance_date'].input_formats = ['%Y-%m-%d']
        for field in self.fields.values():
            css_class = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            field.widget.attrs.setdefault('class', css_class)
