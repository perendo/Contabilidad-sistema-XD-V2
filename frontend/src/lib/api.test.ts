import { afterEach, describe, expect, it, vi } from "vitest";
import { api, fetchApi } from "./api";

describe("api", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("api_error_uses_backend_detail_message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Código de cuenta duplicado" }), {
          status: 409,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const error = await api("/accounts").catch((err: unknown) => err);

    expect(error).toBeInstanceOf(Error);
    expect((error as Error).message).toBe("Código de cuenta duplicado");
  });

  it("api_error_formats_validation_detail_list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({
            detail: [
              { loc: ["body", "date"], msg: "Field required", type: "missing" },
              {
                loc: ["body", "amount"],
                msg: "Input should be a valid number",
                type: "number",
              },
            ],
          }),
          {
            status: 422,
            headers: { "Content-Type": "application/json" },
          }
        )
      )
    );

    const error = await api("/journal-entries", { method: "POST" }).catch(
      (err: unknown) => err
    );

    expect(error).toBeInstanceOf(Error);
    expect((error as Error).message).toBe(
      "Field required; Input should be a valid number"
    );
  });

  it("api_error_exposes_unauthorized_status", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Credenciales inválidas" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const error = await api("/company").catch((err: unknown) => err);

    expect(error).toBeInstanceOf(Error);
    expect(error).toMatchObject({
      message: "Credenciales inválidas",
      status: 401,
    });
  });

  it("api_network_error_has_readable_message", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new TypeError("Failed to fetch"))
    );

    const error = await api("/company").catch((err: unknown) => err);

    expect(error).toBeInstanceOf(Error);
    expect(error).toMatchObject({
      message: "No se pudo conectar con el servidor",
      status: 0,
    });
  });

  it("api_error_formats_string_detail_list", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: ["Error A", "Error B"] }), {
          status: 422,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const error = await api("/accounts").catch((err: unknown) => err);

    expect((error as Error).message).toBe("Error A; Error B");
  });

  it("api_unauthorized_clears_marker_and_redirects", async () => {
    const assign = vi.fn();
    const doc = { cookie: "" };
    vi.stubGlobal("window", { location: { assign } });
    vi.stubGlobal("document", doc);
    vi.stubGlobal("sessionStorage", {
      getItem: () => null,
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Sesión caducada" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    await api("/accounts").catch(() => undefined);

    expect(assign).toHaveBeenCalledWith("/login");
    expect(doc.cookie).toContain("auth_session=");
    expect(doc.cookie).toContain("Max-Age=0");
  });

  it("api_login_401_does_not_redirect_and_keeps_message", async () => {
    const assign = vi.fn();
    const doc = { cookie: "" };
    vi.stubGlobal("window", { location: { assign } });
    vi.stubGlobal("document", doc);
    vi.stubGlobal("sessionStorage", {
      getItem: () => null,
      setItem: vi.fn(),
      removeItem: vi.fn(),
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail: "Credenciales inválidas" }), {
          status: 401,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const error = await api(
      "/auth/login",
      { method: "POST", body: JSON.stringify({ email: "a@b.c" }) },
      { redirectOnUnauthorized: false }
    ).catch((err: unknown) => err);

    expect(assign).not.toHaveBeenCalled();
    expect(doc.cookie).toBe("");
    expect(error).toMatchObject({
      message: "Credenciales inválidas",
      status: 401,
    });
  });

  it("api_preserves_structured_detail_with_readable_message", async () => {
    const detail = { headers: ["Fecha", "Concepto", "Importe"] };
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(JSON.stringify({ detail }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        })
      )
    );

    const error = await api("/bank-imports").catch((err: unknown) => err);

    expect(error).toMatchObject({
      message: "Error 400",
      status: 400,
      detail,
    });
  });

  it("api_empty_error_body_has_readable_fallback", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 500 }))
    );

    const error = await api("/accounts").catch((err: unknown) => err);

    expect((error as Error).message).toBe("Error 500");
  });

  it("api_sends_json_and_company_headers", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("window", {});
    vi.stubGlobal("sessionStorage", { getItem: () => "7" });

    await api("/accounts", { method: "POST", body: "{}" });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.headers).toMatchObject({
      "Content-Type": "application/json",
      "X-Company-Id": "7",
    });
  });

  it("fetchApi_sends_company_id_header", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("window", {});
    vi.stubGlobal("sessionStorage", { getItem: () => "7" });

    await fetchApi("/bank-imports");

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.headers).toMatchObject({ "X-Company-Id": "7" });
  });

  it("fetchApi_sends_content_type_for_json_body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response("{}", { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    vi.stubGlobal("window", {});
    vi.stubGlobal("sessionStorage", { getItem: () => null });

    await fetchApi("/bank-imports", { method: "POST", body: JSON.stringify({}) });

    const init = fetchMock.mock.calls[0][1] as RequestInit;
    expect(init.headers).toMatchObject({ "Content-Type": "application/json" });
  });
});
