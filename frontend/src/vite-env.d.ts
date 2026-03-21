/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_REGISTRATION_CODE: string;
  // 在此添加更多环境变量...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
