# D-009 — Voluntariado da RoboCopa e uso do Vercel Hobby

**Data:** 2026-10-10. **Fato informado pelo responsável:** o desenvolvimento da RoboCopa IFMA é **voluntário e sem remuneração relacionada ao projeto**. **Estado:** caráter não comercial declarado; elegibilidade do Hobby **favorável em princípio**, sem certificação individual do fornecedor.

## Evidência e interpretação atualizada

- [Vercel Terms §4](https://vercel.com/legal/terms): plano Hobby permite uso pessoal ou não comercial.
- [Fair Use Guidelines, Commercial Usage](https://vercel.com/docs/limits/fair-use-guidelines#commercial-usage): uso comercial tem finalidade de ganho financeiro de pessoas envolvidas na produção, inclusive desenvolvedor empregado/consultor remunerado.
- [Resposta pública de Vercel Staff](https://community.vercel.com/t/question-about-commercial-usage/23321/4): projeto voluntário, desenvolvido sem pagamento para organização sem fins lucrativos, pode usar Hobby.
- [Colaboração no Vercel Hobby](https://vercel.com/docs/deployments/troubleshoot-project-collaboration): colaboração gratuita quando o repositório é público; condições distintas para repositórios privados.

**Conclusão:** a situação material declarada para a RoboCopa corresponde ao exemplo favorável. A vinculação a uma instituição pública de ensino não torna o projeto automaticamente comercial. Não se deve presumir remuneração de desenvolvimento apenas porque um colaborador exerce cargo remunerado em outra atividade. A resposta pública é informação do fornecedor para caso semelhante, não licença individual irrestrita.

## Decisão

**Vercel Hobby é a primeira escolha da PWA React/TypeScript no MVP**, desde que se mantenham voluntariado, finalidade não comercial e cumprimento dos Termos e quotas. **Cloudflare Pages é contingência**, não escolha preferencial. **Não exigir resposta escrita individual da Vercel como pré-requisito obrigatório genérico** para desenvolver ou demonstrar o site; consultar caso surjam fatos novos ou dúvida concreta. Não contratar plano Pro sem autorização.

Se a conta for contratada formalmente em nome do IFMA, verificar separadamente a autoridade administrativa para aceitar os Termos e uso institucional de marca. Isso não é uma proibição automática decorrente de uso sem fins lucrativos.

## Pendências HYB-09 antes do deploy oficial

- [x] Registrar circunstâncias do desenvolvimento: voluntário, sem remuneração relacionada, conforme declaração do responsável.
- [x] Comparar condições informadas com Terms, Fair Use e manifestação pública do staff Vercel.
- [ ] Verificar tipo e titularidade de conta, permissões de colaboração Git, quotas e disponibilidade aplicáveis ao evento; registrar eventual autorização administrativa quando for a conta institucional.
- [ ] Ajustar **Team Settings → Data Preferences** para desabilitar Model Training no Hobby, quando aplicável, e verificar ausência de PII, código de aluno, tokens ou chaves privilegiadas nos builds.
- [ ] Registrar resultados da verificação operacional em HYB-09/S08 e realizar deploy somente quando os demais gates de produto e segurança da demonstração permitirem.

**Reavaliar se** houver remuneração específica pelo projeto, contratação, exploração comercial, alteração de termos ou impedimento notificado pela Vercel. Uma eventual mudança de provedor afeta somente frontend estático, não Supabase, banco PostgreSQL nem VMs.

Esta decisão **não** afirma que já houve deploy, autorização institucional de publicação, liberação de estudantes ou homologação de código não confiável. G-PROD continua BLOQUEADO. D-009 atualiza a D-008 e complementa D-006 e ADR-005.
