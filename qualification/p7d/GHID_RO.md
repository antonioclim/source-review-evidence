# P7D — ghid local

Nu este necesară o operaţie manuală pentru continuarea reviziei CodeProbe. Acest candidat rămâne separat de Kitul 1 LP02/v3.2, de audit şi de orice alt proiect.

## Examinare

Extrage candidatul într-un director nou şi scurt. Pe Windows poate fi `C:\CP\P7D`; acesta este un exemplu pentru citirea şi verificarea fişierelor, fără promisiunea executării experimentelor Linux pe Windows. Nu extrage peste P7C şi nu combina versiunile.

Deschide terminalul în directorul cu `VERIFY.py` şi rulează `python -I -S -B VERIFY.py`, apoi `python -I -S -B VERIFY_METADATA.py`. Verificarea arhivei nu certifică automat mediul experimental. Dacă Python lipseşte, nu instala automat o versiune numai pentru obţinerea unui PASS.

Citeşte `README_P7D.md`. Toate cazurile ştiinţifice necesare sunt incluse. Nu trebuie recuperate arhive ale altui proiect.

## Reproducere într-un mediu deja compatibil

Comanda de control al mediului este:

```text
python -I -S -B REPRODUCE.py --preflight-only --output ../CP_preflight
```

O nepotrivire de versiune, platformă sau fişiere păstrează refuzul şi nu lansează experimente. Nu edita hash-uri, platforme sau cele 32 de cazuri pentru a trece verificarea.

Ruta focalizată execută toate cazurile A17/A18, 83 de teste, oracolul, afirmaţiile şi harness-ul istoric:

```text
python -I -S -B REPRODUCE.py --output ../CP_smoke
```

Pentru cele 894 de teste păstrate adaugă `--full` şi o destinaţie diferită:

```text
python -I -S -B REPRODUCE.py --full --output ../CP_full
```

Fiecare destinaţie trebuie să fie nouă şi în afara candidatului. Nu o şterge pentru a forţa o rerulare. Păstrează ieşirea şi logurile oricărei încercări nereuşite.

## Citirea rezultatului

`RECEIPT.json` şi mesajul verificatorului final arată închiderea tehnică. `views/NUMBERS.json`, `views/RESULTS.md` şi cele două CSV-uri păstrează rezultatul ştiinţific. **A17 NOT_MET este rezultatul corect de raportat**, inclusiv când comanda se încheie cu cod zero. Cele trei provocări neeligibile nu dispar, iar controalele exploratorii nu le înlocuiesc.

Q07 rămâne necalificată: noul director de rezultate şi copierea a 145 de fişiere ale dependenţelor folosesc aceeaşi gazdă şi aceeaşi bibliotecă standard. Acest ghid nu cere pornirea unui serviciu remote, instalări, publicare sau încărcări în portal.

O eventuală calificare pe mediu rece necesită o dovadă separată a mediului şi a instalării, conform `qualification/p7d/Q07_REMAINING.md`. Nu există un pas de instalare ascuns în aceste comenzi.
