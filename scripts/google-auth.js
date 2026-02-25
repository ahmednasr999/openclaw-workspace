const { google } = require('googleapis');

const oauth2Client = new google.auth.OAuth2(
  '211696039800-i03vt7qjioffirmmgi4f7br2ao3iomc1.apps.googleusercontent.com',
  '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',
  'http://localhost'
);

const scopes = [
  'https://www.googleapis.com/auth/gmail.readonly',
  'https://www.googleapis.com/auth/youtube.readonly',
  'https://www.googleapis.com/auth/calendar.readonly'
];

const url = oauth2Client.generateAuthUrl({
  access_type: 'offline',
  scope: scopes
});

console.log('=== AUTH URL ===');
console.log(url);
console.log('\n=== INSTRUCTIONS ===');
console.log('1. Open the URL above in your browser');
console.log('2. Login with: nasr.ai.assistant@gmail.com');
console.log('3. Grant permissions');
console.log('4. After login, you will be redirected to http://localhost');
console.log('5. Copy the FULL URL from your browser address bar');
console.log('6. Paste it here');
