# -*- coding: utf-8 -*-
#
# Iris - Email Sender
# Copyright (C) 2026 Marco Lombardo
#
# This program is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or (at your
# option) any later version. It is distributed WITHOUT ANY WARRANTY; see the
# GNU Affero General Public License in LICENSE for details.
#
# A commercial licence, without the AGPL obligations, is available for use in
# proprietary or closed-source products - see COMMERCIAL-LICENSE.md.
"""Minimal translation layer for the whole application.

The module has no third-party dependency and never imports Tkinter, so every
other module (parsers, mailer, GUI) can use it freely.

Usage::

    from .i18n import t, set_language

    set_language("it")
    print(t("status.ready"))

English is the default language; the user preference is stored in
``config.ini`` and applied at start-up.
"""

from typing import Dict, List, Tuple

DEFAULT_LANGUAGE = "en"

#: Supported languages: code -> name shown in the interface.
LANGUAGES: Dict[str, str] = {
    "en": "English",
    "it": "Italiano",
}

_current_language = DEFAULT_LANGUAGE


# ---------------------------------------------------------------------------
# Catalogues
# ---------------------------------------------------------------------------
_EN: Dict[str, str] = {
    # -- window / generic --------------------------------------------------
    "app.version_label": "VERSION {version}",
    "footer.copyright": (
        "© 2026 Marco Lombardo — {app}  |  Licensed under AGPL-3.0  |  Commercial licensing:"
    ),
    "footer.email_hint": "Write for a commercial licence or a quote",
    "footer.email_subject": "{app} — commercial licence enquiry",
    "status.ready": "Ready",
    "dialog.error": "Error",
    "dialog.info": "Information",
    "dialog.warning": "Warning",
    "dialog.confirm": "Confirm",
    # -- tabs --------------------------------------------------------------
    "tab.processing": "PROCESSING",
    "tab.log": "LOG",
    "tab.configuration": "CONFIGURATION",
    # -- configuration tab -------------------------------------------------
    "config.sender_frame": "SENDER",
    "config.email": "EMAIL ADDRESS *",
    "config.server": "SMTP SERVER *",
    "config.port": "SMTP PORT *",
    "config.connection": "CONNECTION TYPE *",
    "config.username": "USERNAME",
    "config.password": "PASSWORD",
    "config.auth_note": "Empty username and password = no authentication",
    "config.language": "LANGUAGE",
    "config.profile": "SENDER PROFILE",
    "config.template_frame": "EMAIL TEMPLATE",
    "config.template": "TEMPLATE",
    "config.save_as": "SAVE AS...",
    "config.delete": "DELETE",
    "config.options_frame": "OPTIONS",
    "config.send_delay": "PAUSE BETWEEN MESSAGES",
    "config.send_delay_hint": "seconds (0 = send without pausing)",
    "config.subject": "SUBJECT *",
    "config.message": "MESSAGE *",
    "config.variables": "Variables: {placeholder}",
    "config.cc": "CC",
    "config.bcc": "BCC",
    "config.attachment": "ATTACHMENTS",
    "config.select_file": "ADD FILES...",
    "config.remove": "REMOVE",
    "config.save": "SAVE CONFIGURATION",
    "config.test_connection": "TEST CONNECTION",
    # -- connection types --------------------------------------------------
    "connection.ssl": "SSL/TLS (port 465)",
    "connection.starttls": "STARTTLS (port 587)",
    "connection.none": "None (port 25)",
    # -- processing tab ----------------------------------------------------
    "actions.file_frame": "FILE SELECTION",
    "actions.select_file": "SELECT THE RECIPIENTS FILE",
    "actions.criteria": (
        "RECOGNITION CRITERIA: • Excel/CSV: one column with the email address and one with "
        "the company name (column order is detected automatically, the header row is ignored) "
        "• PDF/Word/Txt: lines such as 'Company Name, name@domain.com', or an address preceded "
        "by the company name • Supported: PDF, Excel (.xlsx/.xlsm/.xls), CSV, Word (.docx), "
        "Text (.txt)"
    ),
    "actions.list_frame": "RECIPIENTS",
    "actions.col_company": "Company Name",
    "actions.col_email": "Email Address",
    "actions.send_selected": "SEND SELECTED",
    "actions.delete_selected": "DELETE SELECTED",
    "actions.create_only": "CREATE EMAILS ONLY",
    "actions.send_all": "SEND ALL",
    # -- log tab -----------------------------------------------------------
    "logs.frame": "EVENTS",
    "logs.clear": "CLEAR LOG",
    "logs.cleared": "Log cleared",
    # -- file dialogs ------------------------------------------------------
    "filedialog.recipients": "Select the recipients file",
    "filedialog.attachment": "Select the attachment (optional)",
    "filetype.all_supported": "All supported formats",
    "filetype.pdf": "PDF",
    "filetype.excel": "Excel",
    "filetype.csv": "CSV",
    "filetype.word": "Word",
    "filetype.text": "Text",
    "filetype.all": "All files",
    # -- status bar --------------------------------------------------------
    "status.analyzing": "Analyzing file...",
    "status.analysis_done": "Analysis complete: {count} recipients",
    "status.analysis_none": "Analysis complete: no recipients found",
    "status.analysis_error": "Error while analyzing the file",
    "status.operation_running": "An operation is running. Please wait for it to finish.",
    "status.no_recipients": "The recipient list is empty",
    "status.select_recipient": "Select at least one recipient from the list",
    "status.removed": "Removed {count} recipients",
    "status.sending": "Sending {count} emails...",
    "status.send_progress": "Sending... {done}/{total}",
    "status.send_error": "Error while sending the emails",
    "status.creating": "Creating {count} email files...",
    "status.create_error": "Error while creating the email files",
    "status.testing": "Testing the SMTP connection...",
    "status.test_failed": "Connection test failed",
    # -- dialogs -----------------------------------------------------------
    "dialog.select_file_first": "Select a file to analyze",
    "dialog.file_missing": "File {path} does not exist",
    "dialog.no_recipients_title": "No recipients",
    "dialog.no_recipients_body": (
        "No valid email address was found in the selected file.\n\n"
        "Check the format of the document (see the recognition criteria)."
    ),
    "dialog.select_recipient": "Select at least one recipient from the list.",
    "dialog.invalid_config": "Invalid configuration",
    "dialog.confirm_send_all": "Send the email to all {count} recipients in the list?",
    "dialog.confirm_create": (
        "Create the {format} files for all {count} recipients?\n(Nothing will be sent)"
    ),
    "dialog.send_done": "Sending complete",
    "dialog.send_done_errors": "Sending completed with errors",
    "dialog.create_done": "Creation complete",
    "dialog.create_done_errors": "Creation completed with errors",
    "dialog.test_title": "Connection test",
    "dialog.closing_title": "Operation in progress",
    "dialog.closing_body": (
        "An operation is still running.\nDo you want to stop it and close the application?"
    ),
    "dialog.config_saved": "Configuration saved successfully to:\n{path}",
    # -- profiles and templates --------------------------------------------
    "dialog.profile_name_title": "Save sender profile",
    "dialog.profile_name_body": "Name for this sender profile:",
    "dialog.template_name_title": "Save template",
    "dialog.template_name_body": "Name for this template:",
    "dialog.name_required": "Enter a name (letters, digits and spaces).",
    "dialog.profile_overwrite": "A profile named '{name}' already exists. Replace it?",
    "dialog.template_overwrite": "A template named '{name}' already exists. Replace it?",
    "dialog.confirm_delete_profile": "Delete the sender profile '{name}'?",
    "dialog.confirm_delete_template": "Delete the template '{name}'?",
    "dialog.select_profile": "Select a sender profile from the list first.",
    "dialog.select_template": "Select a template from the list first.",
    "dialog.select_attachment": "Select an attachment from the list first.",
    # -- log messages ------------------------------------------------------
    "log.logging_ready": "Logging system initialized. Log file: {path}",
    "log.icon_error": "Could not set the window icon: {error}",
    "log.mail_client_error": "Could not open the mail client ({error}). Write to {email}",
    "log.bootstrap_missing": "ttkbootstrap not available: {error}",
    "log.bootstrap_active": "ttkbootstrap active (theme {theme})",
    "log.bootstrap_fallback": "ttkbootstrap not applied, falling back to standard ttk: {error}",
    "log.bootstrap_unavailable": "ttkbootstrap not available, using standard ttk",
    "log.buttons_fallback": "ttkbootstrap buttons unavailable ({error}); using the standard style.",
    "log.tab_style_error": "Could not apply the tab padding style: {error}",
    "log.file_selected": "File selected: {path}",
    "log.start_analysis": "Starting analysis of file: {path}",
    "log.analysis_page": "Analyzing page {page}...",
    "log.analysis_done": "Analysis complete: {count} recipients found",
    "log.analysis_none": "No valid email address found in the document.",
    "log.analysis_error": "Error while analyzing the file: {error}",
    "log.recipient_removed": "Recipient removed: {company} <{email}>",
    "log.attachment_selected": "Attachment selected: {path}",
    "log.attachment_removed": "Attachment removed: {path}",
    "log.connection_type": "Connection type set to: {value}",
    "log.language_changed": "Language changed to {language}",
    "log.profile_saved": "Sender profile saved: {name}",
    "log.profile_loaded": "Sender profile loaded: {name}",
    "log.profile_deleted": "Sender profile deleted: {name}",
    "log.template_saved": "Template saved: {name}",
    "log.template_loaded": "Template loaded: {name}",
    "log.template_deleted": "Template deleted: {name}",
    "log.profile_error": "Could not save the sender profile: {error}",
    "log.template_error": "Could not save the template: {error}",
    "log.invalid_config": "Invalid configuration: {error}",
    "log.config_saved": "Configuration saved to {path}",
    "log.config_save_error": "Error while saving the configuration: {error}",
    "log.config_load_error": "Error while loading the configuration: {error}",
    "log.config_loaded": (
        "Configuration loaded from {path} (encoding {encoding}): sender={sender}, "
        "server={server}:{port}, connection={connection}"
    ),
    "log.dir_error": "Error while preparing the folder '{path}': {error}",
    "log.emails_cleaned": "Removed {count} previously generated email files.",
    "log.file_created": "{format} file created: {path}",
    "log.create_error": "Error while creating the file for {email}: {error}",
    "log.send_summary_ok": "All {count} emails were sent successfully.",
    "log.send_summary_mixed": "{sent} emails sent, {errors} failed (details in the LOG tab).",
    "log.send_summary_failed": "No email sent: {errors} errors (details in the LOG tab).",
    "log.send_summary_none": "No email sent.",
    "log.create_summary_ok": "Created {count} email files in '{path}'.",
    "log.create_summary_mixed": (
        "Created {count} email files, {errors} errors (details in the LOG tab)."
    ),
    "log.create_summary_failed": "No email file created ({errors} errors).",
    "log.create_stopped": "File creation stopped by the user.",
    # -- mailer ------------------------------------------------------------
    "mailer.connecting": "Connecting to {host}:{port} (mode {mode})...",
    "mailer.starttls": "Enabling secure connection (STARTTLS)...",
    "mailer.insecure": "WARNING: the connection is not encrypted",
    "mailer.no_auth_ext": (
        "WARNING: the server does not advertise AUTH support; sending without authentication."
    ),
    "mailer.authenticating": "Authenticating user {user}...",
    "mailer.no_auth": "Connecting without authentication.",
    "mailer.reconnecting": "SMTP connection lost: reconnecting...",
    "mailer.delay_active": "Pausing {seconds} s between one message and the next.",
    "mailer.sent": "Email sent to {company} <{email}>",
    "mailer.send_error": "ERROR sending to {company} <{email}>: {error}",
    "mailer.aborted": "Blocking error: aborting the batch.",
    "mailer.not_attempted": "Not attempted: a previous blocking error stopped the batch",
    "mailer.stopped": "Sending stopped by the user.",
    "mailer.attachment_added": "Attachment added: {name}",
    "mailer.attachment_missing": "Attachment not found: {path}. Continuing without it.",
    "mailer.attachment_error": (
        "Could not read the attachment '{path}': {error}. Continuing without it."
    ),
    "mailer.test_ok_auth": "Connection successful (authenticated).",
    "mailer.test_ok": "Connection successful (without authentication).",
    # -- validation --------------------------------------------------------
    "validate.sender_missing": "Enter the sender email address in the configuration.",
    "validate.sender_invalid": "The sender address is not valid: {value}",
    "validate.sender_required": "Sender address is missing",
    "validate.host_missing": "Enter the SMTP server in the configuration.",
    "validate.port_missing": "Enter the SMTP port in the configuration.",
    "validate.port_range": "The SMTP port must be a number between 1 and 65535 (value: {value}).",
    "validate.connection_invalid": "Invalid connection type: {value}",
    "validate.credentials": (
        "Username and password must both be filled in or both left empty.\n\n"
        "Both empty: connection WITHOUT authentication\n"
        "Both filled: connection WITH authentication"
    ),
    "validate.subject_missing": "Enter the email subject in the configuration.",
    "validate.body_missing": "Enter the email message in the configuration.",
    "validate.attachment_missing": "The selected attachment does not exist: {path}",
    "validate.recipient_invalid": "Invalid recipient address: {value}",
    "validate.cc_invalid": "Invalid CC address: {value}",
    "validate.bcc_invalid": "Invalid BCC address: {value}",
    "validate.delay_invalid": (
        "The pause between messages must be a number of seconds equal to or greater than 0."
    ),
    "validate.name_required": "A profile or template name cannot be empty.",
    # -- SMTP errors -------------------------------------------------------
    "smtp.auth": (
        "SMTP authentication error: the server rejected the credentials ({error}). "
        "Check the username and password."
    ),
    "smtp.not_supported": (
        "SMTP feature not supported by the server: {error}. If the server does not require "
        "authentication, leave username and password empty."
    ),
    "smtp.recipients_refused": "Recipient refused by the SMTP server: {value}",
    "smtp.sender_refused": "Sender refused by the SMTP server: {value} ({error})",
    "smtp.connect": "Could not connect to the SMTP server: {error}",
    "smtp.disconnected": "The SMTP server closed the connection: {error}",
    "smtp.dns": "DNS error: could not resolve the SMTP server name ({error})",
    "smtp.timeout": "Timeout while communicating with the SMTP server: {error}",
    "smtp.refused": "Connection refused by the SMTP server: {error}",
    "smtp.tls": "TLS/SSL error while connecting to the SMTP server: {error}",
    "smtp.generic": "SMTP error: {error}",
    "smtp.unknown": "Error while sending: {error}",
    # -- parsers -----------------------------------------------------------
    "parsers.missing_pypdf": (
        "pypdf is not installed: PDF files cannot be read (pip install pypdf)"
    ),
    "parsers.missing_openpyxl": (
        "openpyxl is not installed: .xlsx files cannot be read (pip install openpyxl)"
    ),
    "parsers.missing_xlrd": (
        "xlrd is not installed: .xls files cannot be read (pip install 'xlrd>=2.0.1')"
    ),
    "parsers.missing_docx": (
        "python-docx is not installed: .docx files cannot be read (pip install python-docx)"
    ),
    "parsers.unsupported": "Unsupported file format: {ext}. Supported formats: {formats}",
    "parsers.no_extension": "(no extension)",
    "parsers.no_file": "No file selected",
    "parsers.file_missing": "File {path} does not exist",
    "parsers.fallback_company": "Company {domain}",
    "parsers.fallback_company_generic": "Company",
    # -- configuration file ------------------------------------------------
    "configfile.not_found": (
        "Configuration file not found (searched in: {searched}). "
        "It will be created on the first save in {path}."
    ),
    "configfile.read_error": "Could not read {path} with the supported encodings: {error}",
    "configfile.section_missing": "Section [{section}] is missing from {path}.",
    # -- message writer ----------------------------------------------------
    "msgwriter.outlook_error": (
        "Outlook is not usable ({error}): creating the equivalent .eml file instead."
    ),
    "msgwriter.attachment_error": "Could not add the attachment to the MSG file: {error}",
    "msgwriter.remove_error": "Could not remove {name}: {error}",
}

_IT: Dict[str, str] = {
    # -- finestra / generici -----------------------------------------------
    "app.version_label": "VERSIONE {version}",
    "footer.copyright": (
        "© 2026 Marco Lombardo — {app}  |  Distribuito con licenza AGPL-3.0  |  "
        "Licenza commerciale:"
    ),
    "footer.email_hint": "Scrivi per una licenza commerciale o un preventivo",
    "footer.email_subject": "{app} — richiesta di licenza commerciale",
    "status.ready": "Pronto",
    "dialog.error": "Errore",
    "dialog.info": "Informazione",
    "dialog.warning": "Attenzione",
    "dialog.confirm": "Conferma",
    # -- schede ------------------------------------------------------------
    "tab.processing": "ELABORAZIONE",
    "tab.log": "LOG",
    "tab.configuration": "CONFIGURAZIONE",
    # -- scheda configurazione ---------------------------------------------
    "config.sender_frame": "MITTENTE",
    "config.email": "INDIRIZZO EMAIL *",
    "config.server": "SERVER SMTP *",
    "config.port": "PORTA SMTP *",
    "config.connection": "TIPO CONNESSIONE *",
    "config.username": "NOME UTENTE",
    "config.password": "PASSWORD",
    "config.auth_note": "Nome utente e password vuoti = nessuna autenticazione",
    "config.language": "LINGUA",
    "config.profile": "PROFILO MITTENTE",
    "config.template_frame": "TEMPLATE EMAIL",
    "config.template": "MODELLO",
    "config.save_as": "SALVA COME...",
    "config.delete": "ELIMINA",
    "config.options_frame": "OPZIONI",
    "config.send_delay": "PAUSA TRA I MESSAGGI",
    "config.send_delay_hint": "secondi (0 = invio senza pause)",
    "config.subject": "OGGETTO *",
    "config.message": "MESSAGGIO *",
    "config.variables": "Variabili: {placeholder}",
    "config.cc": "CC",
    "config.bcc": "CCN",
    "config.attachment": "ALLEGATI",
    "config.select_file": "AGGIUNGI FILE...",
    "config.remove": "RIMUOVI",
    "config.save": "SALVA CONFIGURAZIONE",
    "config.test_connection": "VERIFICA CONNESSIONE",
    # -- tipi di connessione -----------------------------------------------
    "connection.ssl": "SSL/TLS (porta 465)",
    "connection.starttls": "STARTTLS (porta 587)",
    "connection.none": "Nessuna (porta 25)",
    # -- scheda elaborazione -----------------------------------------------
    "actions.file_frame": "SELEZIONE FILE",
    "actions.select_file": "SELEZIONA IL FILE CON I DESTINATARI",
    "actions.criteria": (
        "CRITERI DI RICONOSCIMENTO: • Excel/CSV: una colonna con l'indirizzo email e una con il "
        "nome azienda (l'ordine delle colonne viene rilevato automaticamente, l'intestazione "
        "viene ignorata) • PDF/Word/Txt: righe tipo 'Nome Azienda, nome@dominio.it' oppure "
        "indirizzo preceduto dal nome azienda • Supportati: PDF, Excel (.xlsx/.xlsm/.xls), CSV, "
        "Word (.docx), Testo (.txt)"
    ),
    "actions.list_frame": "DESTINATARI",
    "actions.col_company": "Nome Azienda",
    "actions.col_email": "Indirizzo Email",
    "actions.send_selected": "INVIA SELEZIONATE",
    "actions.delete_selected": "ELIMINA SELEZIONATE",
    "actions.create_only": "CREA SOLO EMAIL",
    "actions.send_all": "INVIA TUTTE",
    # -- scheda log --------------------------------------------------------
    "logs.frame": "EVENTI",
    "logs.clear": "PULISCI LOG",
    "logs.cleared": "Log puliti",
    # -- finestre di selezione file ----------------------------------------
    "filedialog.recipients": "Seleziona il file con i destinatari",
    "filedialog.attachment": "Seleziona l'allegato (facoltativo)",
    "filetype.all_supported": "Tutti i formati supportati",
    "filetype.pdf": "PDF",
    "filetype.excel": "Excel",
    "filetype.csv": "CSV",
    "filetype.word": "Word",
    "filetype.text": "Testo",
    "filetype.all": "Tutti i file",
    # -- barra di stato ----------------------------------------------------
    "status.analyzing": "Analisi del file in corso...",
    "status.analysis_done": "Analisi completata: {count} destinatari",
    "status.analysis_none": "Analisi completata: nessun destinatario trovato",
    "status.analysis_error": "Errore durante l'analisi del file",
    "status.operation_running": "Operazione in corso. Attendi il completamento.",
    "status.no_recipients": "La lista dei destinatari è vuota",
    "status.select_recipient": "Seleziona almeno un destinatario dalla lista",
    "status.removed": "Rimossi {count} destinatari",
    "status.sending": "Invio di {count} email in corso...",
    "status.send_progress": "Invio in corso... {done}/{total}",
    "status.send_error": "Errore nell'invio delle email",
    "status.creating": "Creazione di {count} email in corso...",
    "status.create_error": "Errore nella creazione dei file email",
    "status.testing": "Verifica della connessione SMTP in corso...",
    "status.test_failed": "Verifica della connessione fallita",
    # -- finestre di dialogo -----------------------------------------------
    "dialog.select_file_first": "Seleziona un file da analizzare",
    "dialog.file_missing": "Il file {path} non esiste",
    "dialog.no_recipients_title": "Nessun destinatario",
    "dialog.no_recipients_body": (
        "Nel file selezionato non è stato trovato alcun indirizzo email valido.\n\n"
        "Verifica il formato del documento (vedi i criteri di riconoscimento)."
    ),
    "dialog.select_recipient": "Seleziona almeno un destinatario dalla lista.",
    "dialog.invalid_config": "Configurazione non valida",
    "dialog.confirm_send_all": "Vuoi inviare l'email a tutti i {count} destinatari in elenco?",
    "dialog.confirm_create": (
        "Vuoi creare i file {format} per tutti i {count} destinatari?\n"
        "(L'invio NON verrà effettuato)"
    ),
    "dialog.send_done": "Invio completato",
    "dialog.send_done_errors": "Invio completato con errori",
    "dialog.create_done": "Creazione completata",
    "dialog.create_done_errors": "Creazione completata con errori",
    "dialog.test_title": "Verifica connessione",
    "dialog.closing_title": "Operazione in corso",
    "dialog.closing_body": (
        "Un'operazione è ancora in corso.\nVuoi interromperla e chiudere l'applicazione?"
    ),
    "dialog.config_saved": "Configurazione salvata con successo in:\n{path}",
    # -- profili e template ------------------------------------------------
    "dialog.profile_name_title": "Salva profilo mittente",
    "dialog.profile_name_body": "Nome per questo profilo mittente:",
    "dialog.template_name_title": "Salva template",
    "dialog.template_name_body": "Nome per questo template:",
    "dialog.name_required": "Inserisci un nome (lettere, cifre e spazi).",
    "dialog.profile_overwrite": "Esiste già un profilo di nome '{name}'. Vuoi sostituirlo?",
    "dialog.template_overwrite": "Esiste già un template di nome '{name}'. Vuoi sostituirlo?",
    "dialog.confirm_delete_profile": "Vuoi eliminare il profilo mittente '{name}'?",
    "dialog.confirm_delete_template": "Vuoi eliminare il template '{name}'?",
    "dialog.select_profile": "Seleziona prima un profilo mittente dall'elenco.",
    "dialog.select_template": "Seleziona prima un template dall'elenco.",
    "dialog.select_attachment": "Seleziona prima un allegato dall'elenco.",
    # -- messaggi di log ---------------------------------------------------
    "log.logging_ready": "Sistema di logging inizializzato. File di log: {path}",
    "log.icon_error": "Impossibile impostare l'icona della finestra: {error}",
    "log.mail_client_error": "Impossibile aprire il client di posta ({error}). Scrivi a {email}",
    "log.bootstrap_missing": "ttkbootstrap non disponibile: {error}",
    "log.bootstrap_active": "ttkbootstrap attivo (tema {theme})",
    "log.bootstrap_fallback": "ttkbootstrap non applicato, uso il tema ttk standard: {error}",
    "log.bootstrap_unavailable": "ttkbootstrap non disponibile, uso ttk standard",
    "log.buttons_fallback": "Pulsanti ttkbootstrap non disponibili ({error}); uso lo stile standard.",
    "log.tab_style_error": "Impossibile applicare lo stile ai tab: {error}",
    "log.file_selected": "File selezionato: {path}",
    "log.start_analysis": "Inizio analisi del file: {path}",
    "log.analysis_page": "Analisi della pagina {page}...",
    "log.analysis_done": "Analisi completata: trovati {count} destinatari",
    "log.analysis_none": "Nessun indirizzo email valido trovato nel documento.",
    "log.analysis_error": "Errore durante l'analisi del file: {error}",
    "log.recipient_removed": "Destinatario rimosso: {company} <{email}>",
    "log.attachment_selected": "Allegato selezionato: {path}",
    "log.attachment_removed": "Allegato rimosso: {path}",
    "log.connection_type": "Tipo di connessione impostato su: {value}",
    "log.language_changed": "Lingua impostata su {language}",
    "log.profile_saved": "Profilo mittente salvato: {name}",
    "log.profile_loaded": "Profilo mittente caricato: {name}",
    "log.profile_deleted": "Profilo mittente eliminato: {name}",
    "log.template_saved": "Template salvato: {name}",
    "log.template_loaded": "Template caricato: {name}",
    "log.template_deleted": "Template eliminato: {name}",
    "log.profile_error": "Impossibile salvare il profilo mittente: {error}",
    "log.template_error": "Impossibile salvare il template: {error}",
    "log.invalid_config": "Configurazione non valida: {error}",
    "log.config_saved": "Configurazione salvata in {path}",
    "log.config_save_error": "Errore durante il salvataggio della configurazione: {error}",
    "log.config_load_error": "Errore durante il caricamento della configurazione: {error}",
    "log.config_loaded": (
        "Configurazione caricata da {path} (encoding {encoding}): mittente={sender}, "
        "server={server}:{port}, connessione={connection}"
    ),
    "log.dir_error": "Errore nella preparazione della cartella '{path}': {error}",
    "log.emails_cleaned": "Rimossi {count} file email generati in precedenza.",
    "log.file_created": "File {format} creato: {path}",
    "log.create_error": "Errore nella creazione del file per {email}: {error}",
    "log.send_summary_ok": "Tutte le {count} email sono state inviate con successo.",
    "log.send_summary_mixed": "{sent} email inviate, {errors} con errori (dettagli nel tab LOG).",
    "log.send_summary_failed": "Nessuna email inviata: {errors} errori (dettagli nel tab LOG).",
    "log.send_summary_none": "Nessuna email inviata.",
    "log.create_summary_ok": "Creati {count} file email in '{path}'.",
    "log.create_summary_mixed": (
        "Creati {count} file email, {errors} errori (dettagli nel tab LOG)."
    ),
    "log.create_summary_failed": "Nessun file email creato ({errors} errori).",
    "log.create_stopped": "Creazione dei file interrotta dall'utente.",
    # -- invio -------------------------------------------------------------
    "mailer.connecting": "Connessione a {host}:{port} (modalità {mode})...",
    "mailer.starttls": "Attivazione della connessione sicura (STARTTLS)...",
    "mailer.insecure": "ATTENZIONE: la connessione non è cifrata",
    "mailer.no_auth_ext": (
        "ATTENZIONE: il server non dichiara il supporto AUTH; invio senza autenticazione."
    ),
    "mailer.authenticating": "Autenticazione dell'utente {user}...",
    "mailer.no_auth": "Connessione senza autenticazione.",
    "mailer.reconnecting": "Connessione SMTP caduta: riconnessione in corso...",
    "mailer.delay_active": "Pausa di {seconds} s tra un messaggio e il successivo.",
    "mailer.sent": "Email inviata a {company} <{email}>",
    "mailer.send_error": "ERRORE nell'invio a {company} <{email}>: {error}",
    "mailer.aborted": "Errore bloccante: interruzione del lotto.",
    "mailer.not_attempted": "Invio non tentato: un errore bloccante ha fermato il lotto",
    "mailer.stopped": "Invio interrotto dall'utente.",
    "mailer.attachment_added": "Allegato aggiunto: {name}",
    "mailer.attachment_missing": "Allegato non trovato: {path}. Procedo senza allegato.",
    "mailer.attachment_error": (
        "Impossibile leggere l'allegato '{path}': {error}. Procedo senza allegato."
    ),
    "mailer.test_ok_auth": "Connessione riuscita (autenticazione effettuata).",
    "mailer.test_ok": "Connessione riuscita (senza autenticazione).",
    # -- validazione -------------------------------------------------------
    "validate.sender_missing": "Inserire l'indirizzo email del mittente nella configurazione.",
    "validate.sender_invalid": "L'indirizzo del mittente non è valido: {value}",
    "validate.sender_required": "Indirizzo del mittente mancante",
    "validate.host_missing": "Inserire il server SMTP nella configurazione.",
    "validate.port_missing": "Inserire la porta SMTP nella configurazione.",
    "validate.port_range": (
        "La porta SMTP deve essere un numero compreso tra 1 e 65535 (valore: {value})."
    ),
    "validate.connection_invalid": "Tipo di connessione non valido: {value}",
    "validate.credentials": (
        "Nome utente e password devono essere entrambi compilati o entrambi vuoti.\n\n"
        "Entrambi vuoti: connessione SENZA autenticazione\n"
        "Entrambi compilati: connessione CON autenticazione"
    ),
    "validate.subject_missing": "Inserire l'oggetto dell'email nella configurazione.",
    "validate.body_missing": "Inserire il messaggio dell'email nella configurazione.",
    "validate.attachment_missing": "L'allegato selezionato non esiste: {path}",
    "validate.recipient_invalid": "Indirizzo del destinatario non valido: {value}",
    "validate.cc_invalid": "Indirizzo CC non valido: {value}",
    "validate.bcc_invalid": "Indirizzo CCN non valido: {value}",
    "validate.delay_invalid": (
        "La pausa tra i messaggi deve essere un numero di secondi maggiore o uguale a 0."
    ),
    "validate.name_required": "Il nome di un profilo o di un template non può essere vuoto.",
    # -- errori SMTP -------------------------------------------------------
    "smtp.auth": (
        "Errore di autenticazione SMTP: credenziali rifiutate dal server ({error}). "
        "Verifica nome utente e password."
    ),
    "smtp.not_supported": (
        "Funzione SMTP non supportata dal server: {error}. Se il server non richiede "
        "autenticazione, lascia vuoti nome utente e password."
    ),
    "smtp.recipients_refused": "Destinatario rifiutato dal server SMTP: {value}",
    "smtp.sender_refused": "Mittente rifiutato dal server SMTP: {value} ({error})",
    "smtp.connect": "Impossibile connettersi al server SMTP: {error}",
    "smtp.disconnected": "Il server SMTP ha chiuso la connessione: {error}",
    "smtp.dns": "Errore DNS: impossibile risolvere il nome del server SMTP ({error})",
    "smtp.timeout": "Timeout nella comunicazione con il server SMTP: {error}",
    "smtp.refused": "Connessione rifiutata dal server SMTP: {error}",
    "smtp.tls": "Errore TLS/SSL nella connessione al server SMTP: {error}",
    "smtp.generic": "Errore SMTP: {error}",
    "smtp.unknown": "Errore durante l'invio: {error}",
    # -- lettura documenti -------------------------------------------------
    "parsers.missing_pypdf": (
        "pypdf non è installato: impossibile leggere i file PDF (pip install pypdf)"
    ),
    "parsers.missing_openpyxl": (
        "openpyxl non è installato: impossibile leggere i file .xlsx (pip install openpyxl)"
    ),
    "parsers.missing_xlrd": (
        "xlrd non è installato: impossibile leggere i file .xls (pip install 'xlrd>=2.0.1')"
    ),
    "parsers.missing_docx": (
        "python-docx non è installato: impossibile leggere i file .docx (pip install python-docx)"
    ),
    "parsers.unsupported": "Formato file non supportato: {ext}. Formati gestiti: {formats}",
    "parsers.no_extension": "(nessuna estensione)",
    "parsers.no_file": "Nessun file selezionato",
    "parsers.file_missing": "Il file {path} non esiste",
    "parsers.fallback_company": "Azienda {domain}",
    "parsers.fallback_company_generic": "Azienda",
    # -- file di configurazione --------------------------------------------
    "configfile.not_found": (
        "File di configurazione non trovato (cercato in: {searched}). "
        "Verrà creato al primo salvataggio in {path}."
    ),
    "configfile.read_error": (
        "Impossibile leggere {path} con gli encoding supportati: {error}"
    ),
    "configfile.section_missing": "Sezione [{section}] assente in {path}.",
    # -- scrittura file email ----------------------------------------------
    "msgwriter.outlook_error": (
        "Outlook non è utilizzabile ({error}): creo il file .eml equivalente."
    ),
    "msgwriter.attachment_error": "Impossibile aggiungere l'allegato al file MSG: {error}",
    "msgwriter.remove_error": "Impossibile rimuovere {name}: {error}",
}

CATALOGUES: Dict[str, Dict[str, str]] = {"en": _EN, "it": _IT}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def normalize_language(code: str) -> str:
    """Return a supported language code, falling back to the default.

    Accepts values such as ``"it"``, ``"IT"`` or ``"it-IT"``.
    """
    if not code:
        return DEFAULT_LANGUAGE
    candidate = str(code).strip().lower().replace("_", "-").split("-")[0]
    return candidate if candidate in CATALOGUES else DEFAULT_LANGUAGE


def set_language(code: str) -> str:
    """Set the active language and return the code actually applied."""
    global _current_language
    _current_language = normalize_language(code)
    return _current_language


def get_language() -> str:
    """Return the active language code."""
    return _current_language


def language_name(code: str) -> str:
    """Return the display name of a language (e.g. ``"Italiano"``)."""
    return LANGUAGES.get(normalize_language(code), LANGUAGES[DEFAULT_LANGUAGE])


def language_choices() -> List[Tuple[str, str]]:
    """Return ``[(code, name), ...]`` for every supported language."""
    return [(code, LANGUAGES[code]) for code in CATALOGUES]


def t(key: str, **kwargs) -> str:
    """Translate ``key`` into the active language.

    Falls back to English and finally to the key itself, so a missing entry
    degrades to something readable instead of raising.
    """
    text = CATALOGUES.get(_current_language, _EN).get(key)
    if text is None:
        text = _EN.get(key, key)
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError, ValueError):
        # A malformed placeholder must never break the interface.
        return text
