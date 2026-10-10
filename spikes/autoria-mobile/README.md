# Laboratório de autoria móvel — S04-T03

**Uso exclusivo do responsável, em localhost. Não exponha para estudantes.** Implementação experimental de editor + RoboDSL + motor Tank Royale 1.4.0, sem modificar o Compose existente.

## Executar no Windows

Abra o Docker Desktop. Na pasta atual do repositório:

```powershell
Set-Location 'G:\projetos\ifma\project-robocopa-ifma'
git fetch origin
git switch feat/s04-mobile-authoring
git pull --ff-only
python scripts/serve_mobile_spike.py
```

Pare a sequência se algum comando Git falhar. Não é necessário recriar .env, instalar Java/Node/Playwright no Windows nem parar o PostgreSQL. O comando prepara as imagens usando o cache e inicia somente o servidor local. Não use o preflight da primeira instalação: seu projeto Compose já existe.

Abra `http://127.0.0.1:18081` no navegador deste computador. O terminal fica ocupado enquanto o laboratório funciona. Ctrl+C encerra o servidor; uma batalha em andamento deve terminar sua limpeza antes da saída. Para reabrir sem mudança de código/imagem: `python scripts/serve_mobile_spike.py --skip-build`.

## Experimento orientado

Carregue sentinela, verifique o código e teste no motor. Veja os pontos e reproduza as posições do replay. Depois carregue explorador e teste novamente. Compare a velocidade média: o placar não é a única evidência de alteração. Modifique uma condição de energia ou distância e execute outra versão. Rascunhos são salvos neste navegador, não inscritos em competição.

Resultados ficam em `.local/mobile-spike/<execucao>/`: programa.robo, ast.json, results.json, preview.json, manifest.json, engine.log e recordings/*.battle.gz. Nenhum desses arquivos deve ser commitado com dados reais. O servidor só serve suas três páginas/rotas estáticas, não a raiz do projeto.

## Celular e limites

A interface é responsiva e será verificada em Chromium com emulação móvel. **127.0.0.1 no celular aponta para o próprio celular**, não para o PC. Não há acesso LAN/público nesta entrega; teste físico requer método de conexão controlado e autorização separados. Emulação não fecha MOB-008 nem a homologação pedagógica.

As batalhas são reais, mas o laboratório não contém cadastro, login de alunos, fila durável, inscrição, ranking de torneio ou sandbox de produção. Servidor Python no host tem acesso à CLI Docker; não é um serviço autorizado para receber requisições públicas. A DSL aceita somente comandos conhecidos e limitados; não envie código Java, JavaScript ou shell.

Mover o Git para outra unidade não move o VHDX do Docker. A construção usa o armazenamento gerenciado pelo Desktop. Não há prune, migração, abertura de portas no roteador nem alteração de outros contêineres.
