from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.contrib.messages import constants
from django.core.exceptions import ValidationError
from django.http import Http404
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods


@require_http_methods(["GET", "POST"])
def cadastro(request):
    if request.method == 'GET':
        return render(request, 'cadastro.html')

    username = request.POST.get('username', '').strip()
    senha = request.POST.get('senha', '')
    confirmar_senha = request.POST.get('confirmar_senha', '')

    if not username:
        messages.add_message(request, constants.ERROR, 'Username é obrigatório.')
        return redirect('cadastro')

    if senha != confirmar_senha:
        messages.add_message(request, constants.ERROR, 'Senha e confirmar senha devem ser iguais.')
        return redirect('cadastro')

    try:
        validate_password(senha)
    except ValidationError as e:
        for erro in e.messages:
            messages.add_message(request, constants.ERROR, erro)
        return redirect('cadastro')

    if User.objects.filter(username=username).exists():
        messages.add_message(request, constants.ERROR, 'Já existe um usuário com esse username.')
        return redirect('cadastro')

    User.objects.create_user(username=username, password=senha)
    messages.add_message(request, constants.SUCCESS, 'Conta criada com sucesso! Faça login.')
    return redirect('login')


@require_http_methods(["GET", "POST"])
def login(request):
    if request.method == 'GET':
        return render(request, 'login.html')

    username = request.POST.get('username', '').strip()
    senha = request.POST.get('senha', '')

    user = authenticate(request, username=username, password=senha)
    if user:
        auth_login(request, user)
        return redirect('chat')

    messages.add_message(request, constants.ERROR, 'Username ou senha inválidos.')
    return redirect('login')


@login_required
@user_passes_test(lambda u: u.is_superuser)
def permissoes(request):
    users = User.objects.filter(is_superuser=False)
    return render(request, 'permissoes.html', {'users': users})


@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_http_methods(["POST"])
def tornar_gerente(request, id):
    from rolepermissions.roles import assign_role
    try:
        user = User.objects.get(id=id)
    except User.DoesNotExist:
        raise Http404()
    assign_role(user, 'gerente')
    return redirect('permissoes')
