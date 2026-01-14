
export enum ConnectionType {
  RDP = 'RDP',
  VPN = 'VPN'
}

export enum VPNProtocol {
  OpenVPN = 'OpenVPN',
  FortiClient = 'FortiClient',
  GlobalProtect = 'Palo Alto GlobalProtect',
  AnyConnect = 'Cisco AnyConnect',
  Citrix = 'Citrix',
  Parallels = 'Parallels'
}

export interface CredentialProfile {
  id: string;
  name: string;
  username: string;
  password?: string;
  domain?: string;
}

export interface Connection {
  id: string;
  name: string;
  type: ConnectionType;
  host: string;
  port: string;
  group?: string;
  username?: string;
  password?: string;
  sso?: boolean;
  lastConnected?: number;
  protocol?: VPNProtocol;
  domain?: string;
  icon?: string;
  credentialId?: string;
  gateway?: string;
}

export interface AppConfig {
  theme: 'light' | 'dark';
  connections: Connection[];
  pythonSync: boolean;
  showDevTools: boolean;
}
