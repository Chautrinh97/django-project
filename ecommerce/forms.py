from django import forms

class CustomerLoginForm(forms.Form):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'mb-0',
                                                                           'placeholder': 'Nhập địa chỉ Email'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'mb-0', 'type':'password',
                                                                 'placeholder': "Nhập mật khẩu"}))

class CustomerRegisterForm(forms.Form):
    name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'mb-0',
                                                                                       'placeholder':'Nhập tên khách hàng'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'mb-0',
                                                                           'placeholder':'Nhập địa chỉ Email'}))
    phone_number = forms.CharField(max_length=11, required=True,
                                   widget=forms.TextInput(attrs={'class': 'mb-0',
                                                                 'placeholder':'Nhập số điện thoại'}))
    password = forms.CharField(min_length=6,max_length=255, required=True,
                               widget=forms.PasswordInput(attrs={'class': 'mb-0', 'type':'password',
                                                                 'placeholder':'Nhập mật khẩu'}))
    confirm_password = forms.CharField(min_length=6,max_length=255, required=True,
                                       widget=forms.PasswordInput(attrs={'class': 'mb-0','type':'password',
                                                                         'placeholder':'Nhập lại mật khẩu'}))
