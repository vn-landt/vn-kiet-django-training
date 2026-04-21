# -*- coding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UsageLog(models.Model):
	objects = None
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='usage_logs')
	usage_date = models.DateField(default=timezone.now)
	upload_count = models.IntegerField(default=0)
	
	class Meta:
		unique_together = ('user', 'usage_date')
