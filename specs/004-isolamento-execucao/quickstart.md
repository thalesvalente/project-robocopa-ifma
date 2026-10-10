# Quickstart seguro — inspeção do planejamento S04-T04

**Somente documentação, sem executar exploits, instalar VM, alterar Docker Desktop ou abrir portas.**

1. Confira que está na branch `docs/s04-t04-isolamento-speckit` e não há alterações locais que possam ser sobrescritas.
2. Leia [spec.md](spec.md) → [clarifications.md](clarifications.md) → [research.md](research.md) → [plan.md](plan.md) → [tasks.md](tasks.md) → [analysis.md](analysis.md).
3. Examine [ameacas-sandbox.md](../../docs/arquitetura/ameacas-sandbox.md), [ADR-004](../../docs/arquitetura/ADR-004-isolamento-execucao.md) e [checklist de gates](checklists/security-gates.md).
4. No PowerShell, dentro do repositório, execute **somente** os validadores sem efeito no host:

```powershell
python scripts/verify_security_spec.py
python -m unittest discover -s tests/planning -v
```

5. A automação do projeto executará também o verificador nativo de pré-requisitos do Spec Kit com `SPECIFY_FEATURE_DIRECTORY=specs/004-isolamento-execucao`, sem criar contêineres.
6. Revisar e ratificar **D1–D5** de `clarifications.md`. Enquanto houver riscos críticos e gates pendentes, **não iniciar** tarefas de implantação/execução de código de alunos.

Se houver erro na validação, tratar como inconsistência de documentação, não como defeito de sandbox já implantada.

## Segurança da operação

- **Não** publicar `http://127.0.0.1:18081` por LAN/túnel/roteador — o servidor Python de laboratório chama Docker na máquina do responsável.
- **Não** executar `docker system prune`, `down -v`, `docker run --privileged` nem migrar VHDX com base nestes documentos.
- Execuções de ataque, saturação e rede devem ser autorizadas separadamente e permanecer em VM/runner descartáveis sem acesso a arquivos pessoais.
- Se uma decisão D1–D5 não for aprovada, registre bloqueio e ajuste arquitetura; não contorne com Docker compartilhado.
