"""Read Yahoo Fantasy Basketball league data and publish sanitized JSON."""
import base64
import datetime as dt
import json
import os
from pathlib import Path
import sys

import requests
import xmltodict

BASE = 'https://fantasysports.yahooapis.com/fantasy/v2'
OUT = Path('public/fantasy-data.json')


def token():
    client_id = os.environ['YAHOO_CLIENT_ID']
    client_secret = os.environ['YAHOO_CLIENT_SECRET']
    refresh_token = os.environ['YAHOO_REFRESH_TOKEN']
    auth = base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
    resp = requests.post('https://api.login.yahoo.com/oauth2/get_token',
        headers={'Authorization': f'Basic {auth}'},
        data={'grant_type': 'refresh_token', 'refresh_token': refresh_token}, timeout=30)
    resp.raise_for_status()
    payload = resp.json()
    if payload.get('refresh_token') and payload['refresh_token'] != refresh_token:
        print('WARNING: Yahoo returned a rotated refresh token. Update the YAHOO_REFRESH_TOKEN GitHub secret.', file=sys.stderr)
        # Do not log the secret; automatic secret updates are not enabled.
    return payload['access_token']


def get(session, path):
    resp = session.get(f'{BASE}/{path}', params={'format': 'json'}, timeout=45)
    resp.raise_for_status()
    return resp.json()


def main():
    league = os.environ['YAHOO_LEAGUE_KEY'].strip()
    if not league or '.' not in league:
        raise ValueError('YAHOO_LEAGUE_KEY must look like 466.l.12345; use your actual league key.')
    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {token()}', 'Accept': 'application/json'})
    endpoints = {
        'settings': f'league/{league}/settings',
        'standings': f'league/{league}/standings',
        'teams': f'league/{league}/teams',
        'scoreboard': f'league/{league}/scoreboard',
        'transactions': f'league/{league}/transactions',
        'free_agents': f'league/{league}/players;status=FA;count=75',
        'waivers': f'league/{league}/players;status=W;count=75',
    }
    data = {'updated_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(), 'league_key': league,
            'source': 'Yahoo Fantasy Sports API', 'endpoints': {}, 'errors': {}}
    for name, endpoint in endpoints.items():
        try:
            data['endpoints'][name] = get(session, endpoint)
        except requests.HTTPError as exc:
            data['errors'][name] = f'HTTP {exc.response.status_code}'
            print(f'WARN {name}: {exc}', file=sys.stderr)
    # Team roster endpoints. Yahoo teams collections can be traversed via team keys.
    teams_payload = data['endpoints'].get('teams', {})
    teams_obj = teams_payload.get('fantasy_content', {}).get('league', [])
    team_keys = []
    if isinstance(teams_obj, list) and len(teams_obj) > 1:
        collection = teams_obj[1].get('teams', {})
        for entry in collection.values():
            if isinstance(entry, dict) and 'team' in entry:
                node = entry['team']
                if isinstance(node, list) and node:
                    for piece in node[0] if isinstance(node[0], list) else []:
                        if isinstance(piece, dict) and 'team_key' in piece:
                            team_keys.append(piece['team_key'])
    data['team_rosters'] = {}
    for key in team_keys:
        try:
            data['team_rosters'][key] = get(session, f'team/{key}/roster')
        except requests.HTTPError as exc:
            data['errors'][f'roster_{key}'] = f'HTTP {exc.response.status_code}'
    if not data['endpoints']:
        raise RuntimeError('No Yahoo endpoints succeeded; refusing to publish empty data.')
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'Wrote {OUT} ({OUT.stat().st_size:,} bytes), rosters={len(team_keys)}, errors={len(data["errors"])}')


if __name__ == '__main__':
    main()
