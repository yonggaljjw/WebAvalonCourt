export async function api(path, method = "GET", body) {
  const response = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response.json();
  if (!response.ok) {
    throw Error(
      typeof data.detail === "string" ? data.detail : "입력값을 확인해주세요.",
    );
  }
  return data;
}
