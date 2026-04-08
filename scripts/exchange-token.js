const { google } = require('googleapis');

const oauth2Client = new google.auth.OAuth2(
  '211696039800-i03vt7qjioffirmmgi4f7br2ao3iomc1.apps.googleusercontent.com',
  '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',
  'http://localhost'
);

const code = '4/0AfrIepBIGIh2vpHccARZ1VszCOFA0zPtnJwe7BG0fRrFNSDRTWA5vWWOxAaI11i4X-hRlg';

oauth2Client.getToken(code, (err, token) => {
  if (err) {
    console.error('Error:', err);
    return;
  }
  console.log('=== ACCESS TOKEN ===');
  console.log(token.access_token);
  console.log('\n=== REFRESH TOKEN ===');
  console.log(token.refresh_token);
  console.log('\n=== SAVE THIS ===');
  console.log('Store these tokens securely!');
});
