# Universo Rebeldia

PWA de **A Rebeldia da Mecatrônica** para transformar conhecimento em projetos pequenos e testáveis.

## Fluxo principal

1. **Ler:** escolha um capítulo do livro. O botão ao final leva à reflexão e registra a leitura.
2. **Refletir:** explique uma ideia com suas palavras e relacione-a a um problema real.
3. **Conectar conceitos:** selecione pelo menos dois conceitos do glossário e descreva como trabalham juntos. Os conceitos referenciados no capítulo aparecem primeiro, sem impedir conexões com outras áreas.
4. **Criar projeto:** a reflexão e a conexão preenchem o problema e a solução inicial. Registre nome, componentes, primeiro teste e resultado observável. Revise os campos e salve.

Cada capítulo tem sua própria reflexão, seleção de conceitos, conexão e rascunho. A página inicial indica o próximo passo. Projetos guardam uma cópia do contexto da leitura, que não muda quando a reflexão original é revisada. Podem ser reabertos, editados e excluídos.

Não há pontuação, rankings, conquistas ou certificações no fluxo. Telas e catálogos de fases anteriores permanecem nos arquivos por compatibilidade, mas suas rotas estão desativadas e não são carregadas nem necessárias ao funcionamento offline. Dados antigos não são removidos; projetos anteriores continuam editáveis.

## Execução

Sem frameworks, CDN, conta ou servidor de aplicação. Na raiz:

```powershell
python -m http.server 8000
```

Abra `http://localhost:8000/app/`. Service workers exigem HTTPS ou localhost. Aguarde a indicação **Pronto para usar offline** antes de desconectar. A primeira visita precisa de conexão: o service worker armazena todas as seis telas ativas, os capítulos completos, o glossário, os scripts, os estilos e os ícones.

No Android/navegadores compatíveis, instale pelo menu ou pelo botão em Configurações. No iOS, use Safari → Compartilhar → Adicionar à Tela de Início. Instalar é opcional; o fluxo também funciona em uma aba.

O cache é isolado pelo escopo da aplicação; as cópias de desenvolvimento e publicação podem coexistir. Uma atualização fica aguardando o fechamento de todas as abas, evitando misturar versões durante a escrita. Ao alterar o shell ou os dados publicados, incremente a versão do cache em `service-worker.js`.

## Persistência

- `localStorage`: leitura, favoritos, anotações, reflexões, conexões e rascunhos. A escrita é imediata, sem esperar um temporizador antes de navegar.
- IndexedDB: projetos salvos, incluindo capítulo de origem, reflexão, IDs dos conceitos, conexão, primeiro teste e resultado esperado.
- Nenhum registro é enviado para uma API. O armazenamento é específico do navegador e da origem; não é sincronização nem garantia contra limpeza de dados.
- Configurações permite exportar/importar um JSON com os registros e preferências, inclusive dados legados. Exporte regularmente e antes de limpar o site.
- Falhas de armazenamento são apresentadas ao leitor. As etapas não avançam quando a gravação local falha.

## Conteúdo e publicação

O Markdown em `capitulos/` continua sendo a fonte de verdade. Não edite os JSON gerados:

```powershell
python generate_app_data.py
python generate_phase2_data.py
```

A publicação existente regenera os catálogos, compila o livro e copia `app/` para `docs/app/`:

```powershell
python publish_site.py
```

Não edite `docs/app/` manualmente. Para copiar somente o shell durante o desenvolvimento, sem regenerar o livro:

```powershell
python -c "import shutil; shutil.copytree('app', 'docs/app', dirs_exist_ok=True, ignore=shutil.ignore_patterns('README.md'))"
```

## Validação

Os testes de navegador em `tests/test_pwa.py` usam `unittest` e Playwright/Chromium. Com essas dependências de desenvolvimento disponíveis:

```powershell
python -m unittest discover -s tests -v
```

Os testes iniciam seu próprio servidor local e verificam: fluxo completo, pré-requisitos, texto em branco, mínimo de dois conceitos, rascunho e projeto após recarga, edição/exclusão, separação por capítulo, exportação/importação, armazenamento indisponível, preservação de projetos antigos, larguras mobile, funcionamento offline e isolamento de cache entre `app/` e `docs/app/`.

Antes de validar recursos secundários, observe com leitores se conseguem, sem ajuda, produzir um projeto com contexto de leitura, problema, conceitos conectados e primeiro teste verificável. Os testes técnicos não substituem essa validação de uso.
