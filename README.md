# Backend Form Member (Python / Flask)

## Env vars

Wajib:

- `API_KEY`
- `PROJECT_ID`
- `DATASET_ID`
- `TABLE_ID_JOIN_MEMBER`

## Cara run lokal

```bash
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt

export API_KEY="VdiQr....Apfo="
export PROJECT_ID="butter-baby-playground"
export DATASET_ID="bb_digital_sandbox"
export TABLE_ID_JOIN_MEMBER="bb_form_member"

python main.py
