from django.db import models
import os
from phonenumber_field.modelfields import PhoneNumberField
from multiselectfield import MultiSelectField
from django.core.files.storage import storages
import uuid


def upload_worker_image(instance, filename):
    ext = filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{ext}"
    return os.path.join("workers", str(instance.id), filename)


class Customer(models.Model):
    gender = [("M", "Male"), ("F", "Female"), ("O", "Others"), ("N", "rather not say")]
    name = models.CharField(
        max_length=100,
        verbose_name="fullName",
    )
    phoneNo = PhoneNumberField(unique=True)
    email = models.EmailField(
        max_length=256,
        unique=True,
    )
    gender = models.CharField(max_length=100, choices=gender, default=gender[-0])
    dob = models.DateField(null=True, blank=True)

    is_working = models.BooleanField(default=False)
    is_online = models.BooleanField(default=False)

    work_id = models.UUIDField(null=True)

    def __str__(self):
        return f"id : {self.id}"


class Worker(models.Model):
    gender = [("M", "Male"), ("F", "Female"), ("O", "Others"), ("N", "rather not say")]

    JobProfiles = [
        ("vehicle", "mechanic"),
        ("carpenter", "wood work"),
        ("electrician", "appliance"),
        ("manual", " labour"),
    ]
    name = models.CharField(
        max_length=100,
    )
    address = models.CharField(
        max_length=500,
    )
    phoneNo = PhoneNumberField(unique=True)
    category = models.CharField(
        max_length=30,
        choices=JobProfiles,
        default=JobProfiles[-1],
    )
    imageURL = models.ImageField(
        upload_to=upload_worker_image,
        storage=storages["minio"],
        null=False,
        blank=False,
        editable=True,
    )
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)

    is_working = models.BooleanField(default=False, editable=True)
    is_online = models.BooleanField(default=False, editable=True)

    work_id = models.UUIDField(null=True, primary_key=False, blank=True, editable=True)

    rating = models.FloatField(default=0, editable=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(choices=gender, default=gender[-1])

    rates = models.JSONField(default=dict, null=True, blank=True, editable=True)

    location = models.CharField(null=True, default="nagpur", editable=True)

    description = models.CharField(max_length=200, blank=True, null=True, editable=True)

    def __str__(self):
        return f"{self.name}-{self.category}"


class History(models.Model):
    id = models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True)
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="historyRecords",
    )
    worker = models.ForeignKey(Worker, on_delete=models.CASCADE)
    action = models.CharField(max_length=30)
    timestmp = models.DateTimeField(auto_now=True)
    is_finished = models.BooleanField(null=False, default=True)

    def __str__(self):
        return f"{self.customer.name}:{self.action}:{self.worker}->{self.timestmp}"
