# Verificação da feature 000

Executar na raiz do repositório, após obter a branch que contém o bootstrap concluído. Requer Python 3.11 ou superior. Estes comandos verificam o planejamento, não executam o produto ou configuram hospedagem.

```sh
python scripts/render_planning.py
python scripts/verify_planning.py
python -m unittest discover -s tests/planning -v
python scripts/verify_deliverables.py
```

## Pré-requisitos nativos do Spec Kit

Linux, macOS ou WSL:

```sh
SPECIFY_FEATURE_DIRECTORY=specs/000-governanca SPECIFY_FEATURE_NO_PERSIST=1 python .specify/scripts/python/check_prerequisites.py --json --require-spec --require-tasks --include-tasks
```

PowerShell:

```powershell
$env:SPECIFY_FEATURE_DIRECTORY = 'specs/000-governanca'
$env:SPECIFY_FEATURE_NO_PERSIST = '1'
python .specify/scripts/python/check_prerequisites.py --json --require-spec --require-tasks --include-tasks
Remove-Item Env:SPECIFY_FEATURE_DIRECTORY
Remove-Item Env:SPECIFY_FEATURE_NO_PERSIST
```

A opção de não persistir evita que esta verificação altere o estado local de seleção da feature. A saída deve identificar o diretório da feature e seus documentos. Sucesso apenas comprova pré-requisitos e presença dos artefatos; não equivale à análise semântica completa dos requisitos ou ao comando `/speckit.analyze` nativo do ChatGPT.

A governança ainda requer inventário no host e ratificação pelo responsável. Não executar scripts de inventário neste ambiente para representar dados de outro computador.
