from django.core.management.base import BaseCommand
from django.contrib.auth.models import User

class Command(BaseCommand):
    help = 'Makes a user a salesperson'

    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username to make salesperson')

    def handle(self, *args, **kwargs):
        username = kwargs['username']
        try:
            user = User.objects.get(username=username)
            user.userprofile.is_salesperson = True
            user.userprofile.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully made {username} a salesperson'))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'User {username} does not exist'))
