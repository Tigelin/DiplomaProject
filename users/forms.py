import os

from django import forms


MAX_FILE_SIZE = 4 * 1024 * 1024

ALLOWED_FILE_TYPES = {
    '.pdf': ['application/pdf'],
    '.doc': ['application/msword'],
    '.docx': [
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ],
    '.xls': ['application/vnd.ms-excel'],
    '.xlsx': [
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    ],
    '.ppt': ['application/vnd.ms-powerpoint'],
    '.pptx': [
        'application/vnd.openxmlformats-officedocument.presentationml.presentation'
    ],
    '.txt': ['text/plain'],
    '.jpg': ['image/jpeg'],
    '.jpeg': ['image/jpeg'],
    '.png': ['image/png'],
}


class LessonFileUploadForm(forms.Form):
    file_name = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Название файла',
        })
    )
    file = forms.FileField(
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': (
                '.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,'
                '.txt,.jpg,.jpeg,.png'
            ),
        })
    )

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        extension = os.path.splitext(uploaded_file.name)[1].lower()

        if uploaded_file.size > MAX_FILE_SIZE:
            raise forms.ValidationError(
                'Размер файла не должен превышать 4 МБ.'
            )

        if extension not in ALLOWED_FILE_TYPES:
            raise forms.ValidationError(
                'Этот формат файла не поддерживается.'
            )

        if uploaded_file.content_type not in ALLOWED_FILE_TYPES[extension]:
            raise forms.ValidationError(
                'Тип содержимого файла не соответствует его расширению.'
            )

        return uploaded_file

    def clean_file_name(self):
        file_name = self.cleaned_data['file_name'].strip()

        if not file_name:
            uploaded_file = self.files.get('file')
            if uploaded_file:
                file_name = uploaded_file.name

        file_name = file_name.replace('\\', '/').split('/')[-1].strip()

        if not file_name:
            raise forms.ValidationError('Укажите название файла.')

        if len(file_name) > 200:
            raise forms.ValidationError(
                'Название файла не должно превышать 200 символов.'
            )

        return file_name
