// REST API 호출 방식을 한 곳으로 통일하는 작은 fetch 래퍼입니다.
// 컴포넌트마다 headers, JSON.stringify, 오류 처리를 반복하지 않게 해줍니다.

export async function api(path, method = "GET", body) {
  // Nginx가 /api 요청을 백엔드로 프록시하므로 브라우저는 같은 origin만 호출합니다.
  const response = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    // GET처럼 body가 없을 때는 body 속성 자체를 넣지 않습니다.
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });

  // 이 프로젝트의 API는 성공/실패 모두 JSON 응답을 반환하도록 구성되어 있습니다.
  const data = await response.json();

  if (!response.ok) {
    // FastAPI가 보내는 detail 문자열을 일반 JavaScript Error로 바꿉니다.
    // 호출자는 try/catch 하나만 사용하면 됩니다.
    throw Error(
      typeof data.detail === "string" ? data.detail : "입력값을 확인해주세요.",
    );
  }

  return data;
}
