import { GoogleGenAI } from "@google/genai";
import { Connection } from "../types.ts";

// Always use a named parameter for the API key and rely on process.env.API_KEY
const ai = new GoogleGenAI({ apiKey: process.env.API_KEY });

export const getSmartConfigHelp = async (connection: Connection) => {
  const prompt = `Provide a professional connection advice or troubleshooting checklist for a ${connection.type} connection. 
  Target: ${connection.host}
  Protocol/Details: ${connection.protocol || 'Default RDP'}
  Return the advice as a structured list of 3-4 key points.`;

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: prompt,
      config: {
        thinkingConfig: { thinkingBudget: 0 }
      }
    });
    // Directly access the .text property from GenerateContentResponse
    return response.text;
  } catch (error) {
    console.error("Gemini Error:", error);
    return "Error retrieving AI assistance.";
  }
};

// Updated generateRdpFile to accept an optional username, defaulting to Administrator
export const generateRdpFile = (connection: Connection, username: string = 'Administrator') => {
  const content = `
screen mode id:i:2
use multimon:i:0
desktopwidth:i:1920
desktopheight:i:1080
session bpp:i:32
winposstr:s:0,3,0,0,800,600
full address:s:${connection.host}
compression:i:1
keyboardhook:i:2
audiocapturemode:i:0
videoplaybackmode:i:1
connection type:i:7
displayconnectionbar:i:1
username:s:${username}
shell working directory:s:
disable wallpaper:i:1
disable full window drag:i:1
disable menu anims:i:1
disable themes:i:0
disable cursor setting:i:0
bitmapcachepersistenable:i:1
audiomode:i:0
redirectprinters:i:1
redirectcomports:i:0
redirectsmartcards:i:1
redirectclipboard:i:1
redirectposdevices:i:0
autoreconnection enabled:i:1
authentication level:i:2
prompt for credentials:i:1
negotiate security layer:i:1
remoteapplicationmode:i:0
alternate shell:s:
shell working directory:s:
gatewayhostname:s:
gatewayusagemethod:i:4
gatewaycredentialssource:i:4
gatewayprofileusagemethod:i:0
promptcredentialonce:i:1
use redirection server name:i:0
rdgiskdcproxy:i:0
kdcproxyname:s:
  `.trim();
  
  const blob = new Blob([content], { type: 'application/rdp' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${connection.name || 'connection'}.rdp`;
  a.click();
  URL.revokeObjectURL(url);
};