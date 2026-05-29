from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from decouple import config


class Command(BaseCommand):
    help = 'Cria o usuário admin inicial a partir das variáveis de ambiente'

    def handle(self, *args, **kwargs):
        username = config('ADMIN_USERNAME', default='admin')
        password = config('ADMIN_PASSWORD', default='admin')
        email = config('ADMIN_EMAIL', default='admin@borgis.com.br')

        if User.objects.filter(username=username).exists():
            self.stdout.write(self.style.WARNING(f'Usuário "{username}" já existe. Ignorado.'))
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superusuário "{username}" criado com sucesso.'))

        if password == 'admin':
            self.stdout.write(
                self.style.WARNING(
                    '⚠ ATENÇÃO: senha padrão "admin" em uso — troque em produção via ADMIN_PASSWORD no .env'
                )
            )
