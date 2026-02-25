const { google } = require('googleapis');
const fs = require('fs');

const ahmedTokens = JSON.parse(fs.readFileSync('/root/.openclaw/workspace/config/ahmed-gmail-tokens.json', 'utf8'));
const oauth2Client = new google.auth.OAuth2(
  '748318689184-7fo6cqr98r33b80u54ikhbpl33kekc6o.apps.googleusercontent.com',
  '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',
  'http://localhost'
);
oauth2Client.setCredentials(ahmedTokens);

const gmail = google.gmail({ version: 'v1', auth: oauth2Client });

const queries = ['LinkedIn', 'recruiter', 'job', 'GulfTalent', 'Bayt', 'foundit', 'interview'];

let results = [];

queries.forEach(query => {
  gmail.users.messages.list({ userId: 'me', q: query, maxResults: 3 }, (err, res) => {
    if (res && res.data && res.data.messages) {
      res.data.messages.slice(0, 2).forEach(msg => {
        gmail.users.messages.get({ userId: 'me', id: msg.id, format: 'metadata', metadataHeaders: ['From', 'Subject', 'Date'] }, (err2, res2) => {
          if (res2 && res2.data) {
            const from = res2.data.payload?.headers?.find(h => h.name === 'From')?.value || '';
            const subject = res2.data.payload?.headers?.find(h => h.name === 'Subject')?.value || '';
            const date = res2.data.payload?.headers?.find(h => h.name === 'Date')?.value || '';
            console.log('- ' + subject.substring(0, 50));
            console.log('  From: ' + from.substring(0, 40));
          }
        });
      });
    }
  });
});
