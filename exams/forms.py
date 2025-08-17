from django import forms
from .models import Question, StudentAnswer

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ['subject', 'text', 'image', 'option1', 'option2', 'option3', 'option4', 'correct_option']
        widgets = {
            'text': forms.Textarea(attrs={'class': 'scientific-input'}),
            'option1': forms.TextInput(attrs={'class': 'scientific-input'}),
            'option2': forms.TextInput(attrs={'class': 'scientific-input'}),
            'option3': forms.TextInput(attrs={'class': 'scientific-input'}),
            'option4': forms.TextInput(attrs={'class': 'scientific-input'}),
            'correct_option': forms.Select(choices=[
                ('', 'Select Correct Option'),
                ('option1', 'Option 1'),
                ('option2', 'Option 2'),
                ('option3', 'Option 3'),
                ('option4', 'Option 4'),
            ]),
        }

class AnswerForm(forms.ModelForm):
    class Meta:
        model = StudentAnswer
        fields = ['selected_option']
        widgets = {
            'selected_option': forms.RadioSelect(choices=[
                ('option1', 'Option 1'),
                ('option2', 'Option 2'),
                ('option3', 'Option 3'),
                ('option4', 'Option 4'),
            ])
        }