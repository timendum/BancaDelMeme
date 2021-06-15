import datetime
import time

import config
import utils

INVESTMENT_DURATION_VAR = utils.investment_duration_string(config.INVESTMENT_DURATION)


def modify_create(username, balance):
    return f"""
*Conto creato!*

Grazie {username} per aver creato un conto /r/BancaDelMeme!

Il tuo saldo iniziale è **{int(balance):,} Mem€**.

Per maggiori informazioni dai un'occhiata alla
[guida di benvenuto](/r/BancaDelMeme/wiki/config/welcome_message).
"""


CREATE_EXISTS_ORG = """
Non capisco se sei troppo entusiasta o stai cercando di truffarmi. Hai già un account!
"""


def _header_investment(amount, initial_upvotes):
    return f"*{int(amount):,} Mem€ investiti @ {initial_upvotes} upvote*\n"


def modify_invest(amount, initial_upvotes, new_balance):
    return (
        _header_investment(amount, initial_upvotes)
        + f"""
Il tuo investimento è ora attivo.
Valuterò il tuo profitto in {INVESTMENT_DURATION_VAR}
e aggiornerò questo stesso commento. Non facciamo che ci perdiamo di vista!

Il tuo saldo attuale è **{int(new_balance):,} Mem€**."""
    )


def modify_invest_return(amount, initial_upvotes, final_upvotes, returned, profit, new_balance):
    text = _header_investment(amount, initial_upvotes)
    text += "\nUPDATE: Il tuo investimento è maturato. "
    if profit > 0:
        text += f"È andato alla grande! Hai guadagnato {int(profit):,} Mem€"
    elif profit < 0:
        text += f"Non è andato bene! Hai perso {int(-profit):,} Mem€"
    else:
        text += f"Sei andato in pari! Hai guadagnato {int(profit):,} Mem€"
    text += f" ({round((profit/amount)*100)}%).\n"
    text += f"\n*{int(returned):,} Mem€ restituiti @ {final_upvotes:,} upvote*\n"
    text += f"\nIl tuo nuovo saldo is **{new_balance:,} Mem€**."
    return text


def modify_invest_capped(amount, initial_upvotes, final_upvotes, returned, profit, new_balance):
    text = _header_investment(amount, initial_upvotes)
    text += "\nUPDATE: Il tuo investimento è maturato. "
    text += f"È andato alla grande! Hai guadagnato {int(profit):,} Mem€"
    text += f" ({round((profit/amount)*100)}%).\n"
    text += """**Congratulazioni,** hai raggiunto il saldo massimo!
Hai trionfato in questa sanguinosa competizione nel marketplace
e il tuo portafoglio è gonfissimo!
Le future generazioni ti ricorderanno come titano degli investimenti.

*"Alessandro pianse, poiché non c'erano altri mondi da conquistare.."* (...ancora)\n"""
    text += f"\nIl tuo nuovo saldo is **{new_balance:,} Mem€** (il saldo massimo)."


def modify_insuff(balance_t):
    return f"""
Non hai abbastanza Mem€ per fare questo investimento.

Il tuo saldo attuale è **{balance_t:,} Mem€**.

Se hai meno di 100 Mem€ e nessun investimento in corso, prova ad inviare `!bancarotta`!
"""


def modify_broke(times):
    return f"""
OOps, sei in bancarotta.

Il tuo saldo è stato resettato a 100 Mem€. Sta attento la prossima volta.

Sei andato in bancarotta {times} volte.
"""


def modify_broke_active(active):
    text = "Hai ancora 1 investmento attivo."
    if active > 1:
        text = f"Hai ancora {active} investmenti attivi."
    return text + "\n\nDovrai attendere che vengano completati."


def modify_broke_money(amount):
    return f"Non sei così povero! Hai ancora **{amount} Mem€**."


HELP_ORG = """
*Benvenuto su BancaDelMeme!*

Io sono un bot che vi aiuterà ad investire in *MEME* e farci una fortuna. Mica come le criptovalute.

Ecco una lista di tutti i comandi che funzionano con me:

### COMANDI GENERALI
- `!attivi` - Mostra gli investimenti attivi
- `!saldo` - Mostra quanti Mem€ si hanno ancora da spendere
- `!bancarotta` - Da usare se si scende sotto i 100 Mem€
- `!crea` - Crea un conto di investimento
- `!aiuto` - Mostra questo messaggio
- `!investi <quantità>` - Permette di investire i propri Mem€
- `!investitutto` - Permette di investire tutti i propri Mem€
- `!mercato` - Mostra il MeMercato Azionario attuale
- `!top` - Mostra i migliori investitori
- `!vendi` - Chiude in anticipo gli investimenti in quel topic (con penalità)
- `!versione` - Mostra la versione attuale del bot
- `!template https://imgur.com/...` **(solo per OP, utile per linkare i template)**

Per avere aiuto su un singolo comando, semplicemente scrivi `!aiuto`

Per altre informazioni e più dettagli,
fai riferimento alla [spiegazione estesa](https://www.reddit.com/r/BancaDelMeme/wiki/regolamento).
"""

BALANCE_ORG = """

"""


def modify_balance(balance, net_worth):
    return f"""Attualmente, il tuo saldo è {balance:,} Mem€**.

In investimenti hai {net_worth - balance:,} Mem€ impegnati,
per un patrimonio totale di {net_worth:,} Mem€."""


ACTIVE_ORG = """


%INVESTMENTS_LIST%
"""


def modify_active(active_investments):
    if not active_investments:
        return "Non hai alcun investimento attivo al momento."

    investments_strings = []
    i = 1
    for inv in active_investments:
        seconds_remaining = inv.time + config.INVESTMENT_DURATION - time.time()
        if seconds_remaining > 0:
            td = datetime.timedelta(seconds=seconds_remaining)
            remaining_string = str(td).split(".")[0] + " rimanenti"
        else:
            remaining_string = "in elaborazione"

        inv_string = (
            f"[#{i}](/r/BancaDelMeme/comments/{inv.post}/_/{inv.comment}): "
            f"{inv.amount:,d} Mem€ @ {inv.upvotes} upvote ({remaining_string})"
        )
        investments_strings.append(inv_string)
        i += 1
    investments_list = "\n\n".join(investments_strings)

    return f"Hai {len(active_investments)} investimenti attivi: \n\n" + investments_list


def modify_min_invest(minim):
    return f"""L'investimento minimo consentito è
di 100 Mem€ o di {round(minim):,} (1% del tuo saldo);
il più alto dei due."""


def modify_market(inves, cap, invs_cap):
    return f"""
Il mercato, in questo momento, ha **{inves:,}** investimenti attivi.

Tutti gli investitori possiedono **{int(cap):,} Mem€**.

Ci sono **{int(invs_cap):,} Mem€** in circolazione su investimenti al momento.
"""


def modify_top(leaders):
    top_string = "Gli investitori con il valore netto più alto (saldo + investimenti attivi):\n\n"
    for leader in leaders:
        top_string = f"{top_string}\n\n{leader.name}: {int(leader.networth):,} Mem€"

    return top_string


TEMPLATE_HINT_ORG = """
---

Psst, %NAME%, puoi scrivere `!template https://imgur.com/...`
per pubblicare il template del tuo post! Alla fine è uno degli scopi di BancaDelMeme! ;)
"""

INVEST_PLACE_HERE_NO_FEE = """
**GLI INVESTIMENTI VANNO QUI - SOLO LE RISPOSTE DIRETTE A QUESTO MESSAGGIO VERRANNO ELABORATE**

Per prevenire spam e altri catastrofi naturali, considero solamente risposte a questo messaggio.
Altri comandi verranno ignorati e potrebbero addirittura venire penalizzati.
Teniamo il nostro MeMercato Azionario bello pulito!

---

Nuovo utente? Ti senti perso e confuso?
Rispondi `!aiuto` a questo messaggio,
o visita la pagina [Wiki](https://www.reddit.com/r/BancaDelMeme/wiki/index)
per una spiegazione più dettagliata.
"""


def invest_no_fee(name):
    return INVEST_PLACE_HERE_NO_FEE + TEMPLATE_HINT_ORG.replace("%NAME%", name)


CLOSED_ORG = """
**La stagione è in chiusura.**

Non è possibile fare nuovi investimenti.
"""

MAINTENANCE_ORG = """
**Il bot è in manutenzione per ragioni tecniche.**

**Dovrebbe tornare online a breve. (Qualche ora)**

**Ci scusiamo per ogni disagio causato.**
"""


TEMPLATE_NOT_OP = """
Spiacente, ma non sei OP
"""

TEMPLATE_ALREADY_DONE = """
Spiacente, ma hai già inviato il link template.
"""

TEMPLATE_NOT_STICKY = """
Spiacente, ma devi rispondere *direttamente* al messaggio stickato del bot.
"""

TEMPLATE_OP = """
---

OP %NAME% ha postato *[IL LINK AL TEMPLATE](%LINK%)*, Evviva!
"""


def modify_template_op(link, name):
    return f"""---

OP {name} ha postato *[IL LINK AL TEMPLATE]({link})*, Evviva!"""


def modify_deploy_version(date):
    return f"""
La versione corrente del bot è stata installata il `{date}`
"""


TEMPLATE_SUCCESS = """
Template postato con successo! Grazie per aver reso /r/BancaDelMeme un posto migliore!
"""


def modify_sell_investment(num_investments, taxes):
    if num_investments < 1:
        return "Nessun investimento attivo trovato in questo post"
    params = {"il": "l", "agg": "o", "verb": "è", "tuo": "", "verr": "à"}
    if num_investments > 1:
        params = {"il": "", "agg": "i", "verb": "sono", "tuo": "i", "verr": "anno"}
    params["taxes"] = utils.formatNumber(taxes)
    return """
I{il} tuo{tuo} investiment{agg} {verb} stat{agg} decrementat{agg} di {taxes} Mem€ e chius{agg}.


A breve i{il} comment{agg} verr{verr} aggiornat{agg} con il risultato.
""".format(
        **params
    )


def modify_oc_return(profit):
    return f"""\n\n---\n\nGrazie del tuo OC!  
Per premiarti ti è stato accreditato un bonus
pari all'1% degli investimenti (non tuoi) su questo post.

Hai guadagnato cosi {int(profit):,d} Mem€"""


def modify_oc_capped():
    return """\n\n---\n\nGrazie del tuo OC!  
Per premiarti ti è stato accreditato un bonus
pari all'1% degli investimenti su questo post (ma non i tuoi).

Hai cosi raggiunto il saldo massimo!
Hai trionfato in questa sanguinosa competizione nel marketplace
e il tuo portafoglio è gonfissimo!
Le future generazioni ti ricorderanno come titano degli investimenti.

*"Alessandro pianse, poiché non c'erano altri mondi da conquistare.."""


def cmd_sconosciuto():
    return """Non conosco il comando che mi hai inviato, il tuo messaggio è stato ignorato."""


def rimozione(rule) -> str:
    return f"""Il tuo post è stato rimosso
perché non rispetta la regola {rule}.

Controlla [le regole](/r/BancaDelMeme/about/rules/), sono poche ma importanti.  
Se hai dubbi [contattaci](/message/compose/?to=/r/BancaDelMeme)."""
