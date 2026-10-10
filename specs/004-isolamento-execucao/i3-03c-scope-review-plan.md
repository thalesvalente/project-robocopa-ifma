# I3-03C H01 — revalidar escopo de reservas e recibos

**Data:** 2026-10-10. **Momento:** revisão após lote cb785934 com 29 integrações PASS; plano publicado ANTES do patch. **Achado:** a validação credencial.scope=worker.scope nega a credencial antiga após trocar o worker de escopo, mas um token NOVO no novo escopo poderia enviar IDs/fence de uma reserva antiga daquele mesmo worker. O helper legado lock_lease valida identidade/tentativa/fence, não compara escopo do job ao novo escopo. Recibo antigo também deve ser recusado quando o worker mudar de escopo. Não presumir isolamento por somente o teste da credencial velha.

## Correção delimitada

Na migration003, preservar 001/002 e acrescentar verificação de escopo de recibo antes de qualquer retorno idempotente, inclusive retorno vazio/fail. Para start/heartbeat/fail, validar lease sob lock e exigir job.scope_id=worker.scope_id antes da operação; repetir a verificação em replay de claim/start/heartbeat. Novo worker escopo não pode operar nem reaver dados do escopo anterior. Erro sanitizado STALE_LEASE.

Acrescentar testes reais com uma reserva lab-a, mudar o worker para lab-b, emitir token novo lab-b e negar: (a) start/heartbeat/fail daquela reserva, sem mudar estado; (b) replay de request_id antigo, mesmo com credencial atualmente válida. Preservar positivos de rotação sem mudança de escopo. Toda assertiva de fechamento CW depende de nova execução HTTPS/Deno/PostgreSQL e regressões.

Esta alteração não cria cadastro multiescola, nova função pública ou permissão de aluno. É requisito já previsto de isolamento entre escopos do canal de serviço. I3-03 integral, G-DEMO e G-PROD permanecem abertos.
