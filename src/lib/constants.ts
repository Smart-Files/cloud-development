
const { MODE } = import.meta.env;

export const BASE_URL = MODE == "development" ? "http://localhost:8080/" : "https://smartfile-sever-test-3-zaq4skcvqq-uc.a.run.app/";
export const WS_URL = MODE == "development" ? "ws://localhost:8080/ws/" : "wss://smartfile-sever-test-3-zaq4skcvqq-uc.a.run.app/ws/";