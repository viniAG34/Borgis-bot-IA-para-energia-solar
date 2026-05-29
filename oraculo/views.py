import json
import logging

from django.contrib import messages as msg
from django.contrib.auth.decorators import login_required
from django.contrib.messages import constants
from django.http import Http404, StreamingHttpResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_http_methods
from rolepermissions.checkers import has_role

from .utils import consultar_ia_stream, construir_vectorstore

logger = logging.getLogger(__name__)


@login_required
def chat(request):
    return render(request, 'chat.html')


@login_required
@require_GET
def stream_response(request):
    """Endpoint SSE — envia a resposta da IA token a token."""
    _MAX_LEN = 1000
    pergunta = request.GET.get('pergunta', '').strip()
    if not pergunta:
        return StreamingHttpResponse(
            iter([f"data: {json.dumps({'erro': 'Pergunta vazia.'})}\n\n"]),
            content_type='text/event-stream',
        )
    if len(pergunta) > _MAX_LEN:
        return StreamingHttpResponse(
            iter([f"data: {json.dumps({'erro': f'Pergunta muito longa (máx. {_MAX_LEN} caracteres).'})}\n\n"]),
            content_type='text/event-stream',
        )

    def _event_stream():
        try:
            for token in consultar_ia_stream(pergunta):
                yield f"data: {json.dumps({'token': token})}\n\n"
        except Exception as exc:
            logger.exception("Erro no stream_response: %s", exc)
            yield f"data: {json.dumps({'erro': 'Erro ao processar a pergunta. Tente novamente.'})}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    response = StreamingHttpResponse(_event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@login_required
@require_http_methods(["GET", "POST"])
def treinar_ia(request):
    if not (request.user.is_superuser or has_role(request.user, 'gerente')):
        raise Http404()

    if request.method == 'POST':
        try:
            construir_vectorstore()
            msg.add_message(request, constants.SUCCESS, 'Base de conhecimento reconstruída com sucesso!')
        except Exception as exc:
            logger.exception("Erro ao reconstruir vectorstore: %s", exc)
            msg.add_message(request, constants.ERROR, 'Erro ao reconstruir a base. Verifique os logs do servidor.')

    return render(request, 'treinar_ia.html')


@login_required
def ver_fontes(request, id):
    return render(request, 'ver_fontes.html')
