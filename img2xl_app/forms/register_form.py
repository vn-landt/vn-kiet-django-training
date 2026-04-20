# -*- coding: utf-8 -*-

from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegisterForm(UserCreationForm):
	# Thêm trường email vào form
	email = forms.EmailField(
		required=True,
		label=u"Email",
		widget=forms.EmailInput(attrs={'placeholder': u'example@gmail.com'})
	)
	
	class Meta:
		model = User
		# Lưu ý: UserCreationForm mặc định đã quản lý password1 và password2 bên trong
		fields = ("username", "email")
	
	# Thứ tự hiển thị: Username -> Password -> Confirm Password -> Email
	field_order = ['username', 'password1', 'password2', 'email']
	
	def __init__(self, *args, **kwargs):
		super(RegisterForm, self).__init__(*args, **kwargs)
		# Tùy chỉnh Label cho các trường mật khẩu của UserCreationForm để thân thiện hơn
		self.fields['username'].widget.attrs.update({'placeholder': u'Tên đăng nhập'})
		self.fields['password1'].label = u"Mật khẩu"
		self.fields['password1'].widget.attrs.update({'placeholder': u'Nhập mật khẩu'})
		self.fields['password2'].label = u"Xác nhận mật khẩu"
		self.fields['password2'].widget.attrs.update({'placeholder': u'Nhập lại mật khẩu'})
	
	def clean_email(self):
		"""Làm sạch email và kiểm tra trùng lặp phía Server"""
		email = self.cleaned_data.get('email')
		if email:
			email = email.lower().strip()
			# Kiểm tra trùng lặp email (bảo mật lớp cuối cùng)
			if User.objects.filter(email=email).exists():
				raise forms.ValidationError(u"Email này đã tồn tại trên hệ thống.")
		return email
	
	def clean(self):
		"""
		Kiểm tra bổ sung nếu cần.
		Mặc định UserCreationForm đã kiểm tra password1 và password2 có khớp nhau không.
		"""
		cleaned_data = super(RegisterForm, self).clean()
		return cleaned_data
