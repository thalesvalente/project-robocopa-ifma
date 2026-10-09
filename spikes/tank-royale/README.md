# Tank Royale — experimento de batalha real (S04-T02)

Executa **Walls v1.0 contra Spin Bot v1.0**, ambos oficiais, em cinco rounds Classic usando Tank Royale **1.4.0**. Não é o portal RoboCopa, não abre interface gráfica e não aceita código de participantes.

## Executar no Windows

Docker Desktop deve estar iniciado no modo Linux. Python e Git já existentes bastam; Java, Maven e dependências Python não precisam ser instalados no Windows.

No PowerShell, entre na cópia do projeto e atualize a branch:

```powershell
Set-Location 'G:\projetos\ifma\project-robocopa-ifma'
git fetch origin
git switch feat/s04-tank-royale-spike
git pull --ff-only
python scripts/run_tank_spike.py
```

Se algum comando Git falhar, pare e revise antes de executar o seguinte. Não use reset, clean ou force para contornar alterações locais. Não é necessário recriar `.env`, parar PostgreSQL ou executar novamente `preflight_local.py`: aquele preflight pertence à primeira instalação do Compose, não a este experimento.

O comando constrói a imagem, verifica os hashes dos arquivos oficiais, executa a batalha e valida os resultados/replay. Na primeira construção haverá downloads das bases Python/Java e dos artefatos oficiais. As imagens e o cache usam espaço no **armazenamento do Docker Desktop**; a pasta do projeto estar em G: não comprova que o VHDX esteja nessa unidade. Nenhuma migração ou limpeza global é realizada.

Para repetir sem reconstruir, somente após sucesso e sem alterações no código/imagem:

```powershell
python scripts/run_tank_spike.py --skip-build
```

## Saídas por execução

Cada chamada cria uma pasta nova `.local/tank-royale/<data-uuid>/` (ignorada pelo Git):

| Arquivo | Conteúdo |
|---|---|
| `results.json` | Nomes, versões, rounds, pontos e colocações retornados pelo motor |
| `recordings/*.battle.gz` | Replay oficial; gzip com eventos JSON do motor |
| `engine.log` | Eventos resumidos e diagnóstico; não é placar simulado |
| `manifest.json` | PASS/FAILED, ambiente, imagem, hashes, controles efetivos e limpeza |
| `build.log` | Diagnóstico de construção, quando não usado `--skip-build` |

A saída final deve indicar `PASS: .local/tank-royale/...`. As pontuações podem variar; o teste exige conclusão e evidência, não que um vencedor ou placar específico se repita. Não há seed fixada neste experimento.

Em erro, consulte `manifest.json` e o log da etapa. `runtime.stream` pode ser preservado quando a batalha/exportação falhar. O executor remove **apenas o contêiner descartável criado por sua chamada**; a imagem permanece para reutilização. Não execute `docker system prune` nem `down -v`.

## Isolamento do experimento

O controlador usa Docker no host, mas o contêiner não recebe socket Docker, senha do banco, `.env`, pasta pessoal ou diretório de projeto. Runtime: rede `none`, nenhuma porta publicada, UID 10001, raiz read-only, capabilities removidas, no-new-privileges, 2 CPUs, 2 GiB e 256 PIDs. Saídas são transferidas por stdout antes de o tmpfs desaparecer; não há montagem de diretórios do host.

**Isso não é uma aprovação de sandbox para código hostil.** Motor, booter e bots confiáveis compartilham o contêiner deste experimento. Isolamento de alunos entre si e contra a plataforma pertence a S04-T04/S06, ainda pendente.

## Evidência já obtida

Duas batalhas reais passaram no [run 38004097096](https://github.com/thalesvalente/project-robocopa-ifma/actions/runs/38004097096), em runner Ubuntu do GitHub. Veja [relatório](../../docs/arquitetura/spike-motor.md) e [evidência estruturada](../../docs/qualidade/evidencias/TANK-ROYALE-CI.json). A reprodução deste spike no Windows do responsável ainda deve ser registrada separadamente.

[Origem/licença dos componentes](NOTICE.md) · [Spec Kit](../../specs/002-tank-royale/spec.md)
