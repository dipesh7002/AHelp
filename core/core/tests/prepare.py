from authentication.models import CommonUser


def create_super_user(email="dipesh@gmail.com", password="dipesh") -> CommonUser:
    user = CommonUser.objects.create(email=email, password=password)
    user.is_staff = True
    user.is_superuser = True
    user.save()
