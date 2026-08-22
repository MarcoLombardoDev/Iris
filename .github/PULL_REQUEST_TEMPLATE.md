## Descrizione

<!-- Cosa cambia e perché. Se corregge un problema, descrivere il sintomo osservato. -->

## Tipo di modifica

- [ ] Correzione di un errore
- [ ] Nuova funzionalità
- [ ] Miglioria (prestazioni, leggibilità, interfaccia)
- [ ] Solo documentazione

## Verifiche

- [ ] `python -m pytest tests` passa (su Linux: `xvfb-run -a python -m pytest tests`)
- [ ] Le correzioni di errori sono coperte da un test che fallisce senza la modifica
- [ ] `CHANGELOG.md` aggiornato
- [ ] Documentazione aggiornata se il comportamento è cambiato
- [ ] Se sono state toccate build o dipendenze: `python build.py` eseguito e
      eseguibile prodotto avviato con esito positivo

## Note per chi revisiona

<!-- Punti a cui prestare attenzione, alternative valutate, limiti noti. -->
