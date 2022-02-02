from django import forms
from .models import Post, Comment, Group


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ('text', 'group', 'image')

    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < 7:
            raise forms.ValidationError('В посте должно быть '
                                        'более 6 символов!')
        elif data[0].islower():
            raise forms.ValidationError('Пост должен начинаться '
                                        'с заглавной буквы!')
        return data


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ('text',)

    def clean_text(self):
        data = self.cleaned_data['text']
        if len(data) < 3:
            raise forms.ValidationError('В комментарии должно быть '
                                        'более 2 символов!')
        elif data[0].islower():
            raise forms.ValidationError('Комментарий должен начинаться '
                                        'с заглавной буквы!')
        return data


class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ('title', 'slug', 'description')

    def clean_title(self):
        data = self.cleaned_data['title']
        if len(data) < 3:
            raise forms.ValidationError('В названии должно быть '
                                        'более 2 символов!')
        elif data[0].islower():
            raise forms.ValidationError('Название группы должно начинаться '
                                        'с заглавной буквы!')
        return data

    def clean_slug(self):
        data = self.cleaned_data['slug']
        if len(data) < 3:
            raise forms.ValidationError('В идентификаторе должно быть '
                                        'более 2 символов!')
        elif not data.islower():
            raise forms.ValidationError('В идентификаторе не должно быть '
                                        'заглавных букв!')
        return data

    def clean_description(self):
        data = self.cleaned_data['description']
        if len(data) < 6:
            raise forms.ValidationError('В описании должно быть '
                                        'более 5 символов!')
        elif data[0].islower():
            raise forms.ValidationError('Описание должно начинаться '
                                        'с заглавной буквы!')
        return data
