/** @odoo-module **/
/**
 * pase_lista_pivot.js
 * ====================
 * Pase de Lista — vista matricial OWL para Odoo 17+.
 *
 * Regla de solo lectura por sesión:
 *   • fecha de sesión < fecha de sesión más reciente  →  columna BLOQUEADA (icono estático)
 *   • fecha de sesión = fecha de sesión más reciente  →  EDITABLE
 *   • actividad finalizada                            →  TODO bloqueado
 *
 * La propiedad `bloqueada` se calcula en loadData() y se guarda en cada
 * entrada del array `state.sesiones` como objeto { iso, label, bloqueada }.
 * Así el template nunca necesita llamar métodos que puedan fallar.
 */

import { registry }   from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, xml } from "@odoo/owl";

// ── Normaliza lo que devuelve Odoo a "YYYY-MM-DD" string ───────────────────
// orm.searchRead puede devolver Date objects o strings según la versión/campo
function toISO(val) {
    if (!val) return "";
    if (typeof val === "string") return val.slice(0, 10);   // ya es string
    if (val instanceof Date)    return val.toISOString().slice(0, 10);
    return String(val).slice(0, 10);
}

// ─────────────────────────────────────────────────────────────────────────────

class PaseListaPivot extends Component {

    static props = ["action", "actionId?", "className?"];

    static template = xml/* xml */`
<div class="o_pase_lista_pivot_view h-100" style="padding:16px; overflow:auto;">

    <!-- Cabecera -->
    <div class="d-flex align-items-center mb-3 gap-2 flex-wrap">
        <h4 class="mb-0 me-2">Pase de Lista</h4>
        <span t-if="state.readonly" class="badge text-bg-secondary">Solo lectura</span>
        <button t-if="!state.loading"
                class="btn btn-sm btn-outline-primary ms-auto"
                t-on-click="reload">↻ Actualizar</button>
        <button t-if="!state.loading and state.sesiones.length > 0"
                class="btn btn-sm btn-success ms-2"
                t-on-click="exportarExcel"
                t-att-disabled="state.exportando ? 'disabled' : false"
                style="display:inline-flex; align-items:center; gap:6px;">
            <t t-if="state.exportando">
                <span class="spinner-border spinner-border-sm"/>
                Exportando…
            </t>
            <t t-else="">
                ⬇ Exportar Excel
            </t>
        </button>
    </div>

    <!-- Cargando -->
    <t t-if="state.loading">
        <div class="text-muted py-4 text-center">
            <span class="spinner-border spinner-border-sm me-2"/>Cargando sesiones…
        </div>
    </t>

    <!-- Sin sesiones -->
    <t t-elif="state.sesiones.length === 0">
        <div class="alert alert-info">
            Aún no hay sesiones registradas.
            Use el botón <strong>Nueva Sesión</strong> para crear la primera.
        </div>
    </t>

    <!-- ── Tabla ─────────────────────────────────────────────────────── -->
    <t t-else="">
        <div style="overflow-x:auto;">
            <table class="table table-bordered table-sm align-middle"
                   style="width:auto; min-width:400px;">

                <!-- Encabezados (una columna por sesión) -->
                <thead class="table-light">
                    <tr>
                        <th style="min-width:180px; white-space:nowrap;">Estudiante</th>

                        <t t-foreach="state.sesiones" t-as="ses" t-key="ses.iso">
                            <th t-att-style="'text-align:center; min-width:105px; white-space:nowrap;'
                                            + (ses.bloqueada ? ' color:#6c757d;' : '')"
                                t-att-title="ses.bloqueada
                                             ? 'Sesión cerrada — existe una sesión posterior'
                                             : 'Sesión más reciente — editable'">
                                <t t-esc="ses.label"/>
                                <t t-if="ses.bloqueada">
                                    <span style="font-size:.75em; margin-left:3px;" title="Solo lectura">🔒</span>
                                </t>
                            </th>
                        </t>

                        <th style="text-align:center; min-width:90px;">Asistencias</th>
                    </tr>
                </thead>

                <!-- Filas (una por estudiante) -->
                <tbody>
                    <t t-foreach="state.filas" t-as="fila" t-key="fila.partner_id">
                        <tr>
                            <td style="white-space:nowrap; font-weight:500;">
                                <t t-esc="fila.nombre"/>
                            </td>

                            <t t-foreach="state.sesiones" t-as="ses" t-key="ses.iso">
                                <t t-set="celda" t-value="fila.celdas[ses.iso]"/>

                                <!-- Celda bloqueada (sesión anterior a la más reciente, o actividad finalizada) -->
                                <td t-if="ses.bloqueada or state.readonly"
                                    style="text-align:center; background:#f8f9fa;"
                                    title="Sesión cerrada — no modificable">
                                    <t t-if="celda and celda.asistencia_id">
                                        <span style="font-size:1.2em;">
                                            <t t-if="celda.presente">✅</t>
                                            <t t-else="">❌</t>
                                        </span>
                                    </t>
                                    <t t-else="">
                                        <span class="text-muted">—</span>
                                    </t>
                                </td>

                                <!-- Celda editable (sesión más reciente) -->
                                <td t-else="" style="text-align:center;">
                                    <t t-if="celda and celda.asistencia_id">
                                        <div class="form-check form-switch d-flex justify-content-center m-0">
                                            <input
                                                class="form-check-input"
                                                type="checkbox"
                                                role="switch"
                                                t-att-checked="celda.presente ? 'checked' : false"
                                                t-on-change="(ev) => this.onToggle(ev, fila, ses.iso)"
                                                style="cursor:pointer; width:2.8em; height:1.4em;"
                                            />
                                        </div>
                                    </t>
                                    <t t-else="">
                                        <span class="text-muted">—</span>
                                    </t>
                                </td>

                            </t>

                            <!-- Total de la fila -->
                            <td style="text-align:center; font-weight:600;">
                                <t t-esc="contarFila(fila)"/>
                                <span class="text-muted" style="font-weight:400;">
                                    /<t t-esc="state.sesiones.length"/>
                                </span>
                            </td>
                        </tr>
                    </t>
                </tbody>

                <!-- Fila de totales -->
                <tfoot>
                    <tr class="table-light fw-bold">
                        <td>Total presentes</td>
                        <t t-foreach="state.sesiones" t-as="ses" t-key="ses.iso">
                            <td style="text-align:center;">
                                <t t-esc="contarCol(ses.iso)"/>
                            </td>
                        </t>
                        <td/>
                    </tr>
                </tfoot>
            </table>
        </div>

        <!-- Leyenda -->
        <div class="mt-2 text-muted small d-flex gap-3 flex-wrap align-items-center">
            <span>✅ Presente (cerrado)</span>
            <span>❌ Ausente (cerrado)</span>
            <span class="d-flex align-items-center gap-1">
                <input type="checkbox" checked="" disabled="" class="form-check-input"
                       style="width:2.4em; height:1.2em; pointer-events:none;"/>
                Presente (editable)
            </span>
            <span class="d-flex align-items-center gap-1">
                <input type="checkbox" disabled="" class="form-check-input"
                       style="width:2.4em; height:1.2em; pointer-events:none;"/>
                Ausente (editable)
            </span>
            <span>🔒 Sesión cerrada</span>
            <span>— Sin registro</span>
        </div>
    </t>

    <!-- Toast de confirmación/error -->
    <t t-if="state.toast.msg">
        <div class="position-fixed bottom-0 end-0 p-3" style="z-index:9999; pointer-events:none;">
            <div class="toast show"
                 t-att-class="state.toast.ok ? 'text-bg-success' : 'text-bg-danger'"
                 role="status" style="min-width:200px;">
                <div class="toast-body"><t t-esc="state.toast.msg"/></div>
            </div>
        </div>
    </t>

</div>
    `;

    // ── Setup ─────────────────────────────────────────────────────────────
    setup() {
        this.orm = useService("orm");

        this.state = useState({
            loading:  true,
            sesiones: [],       // [{ iso, label, bloqueada }, ...]
            filas:    [],       // [{ partner_id, nombre, celdas:{iso:{asistencia_id,presente}} }]
            readonly: false,
            toast:    { msg: "", ok: true },
            exportando: false,
        });

        onWillStart(() => this.loadData());
    }

    get actividadId() {
        const ctx = this.props.action?.context || {};
        return ctx.default_actividad_id || ctx.active_id || null;
    }

    // ── Carga y construye la estructura completa ───────────────────────────
    async loadData() {
        this.state.loading = true;
        const aid = this.actividadId;
        if (!aid) { this.state.loading = false; return; }

        try {
            // 1. Registros de asistencia
            const records = await this.orm.searchRead(
                "actividad.asistencia",
                [["actividad_id", "=", aid]],
                ["id", "fecha", "presente", "partner_id", "inscripcion_id"],
                { order: "fecha asc, partner_id asc" }
            );

            // 2. Estado de la actividad
            const [actividad] = await this.orm.read(
                "actividad.complementaria",
                [aid],
                ["estado_code", "certificates_generated", "inscripcion_ids"]
            );
            const readonly = actividad.estado_code === "finalizada"
                          || !!actividad.certificates_generated;

            // 3. Normalizar fechas a "YYYY-MM-DD" string
            const fechasISO = [...new Set(records.map(r => toISO(r.fecha)))].sort();

            // 4. La sesión más reciente (última en orden ascendente) es la editable.
            //    Todas las anteriores quedan bloqueadas.
            const ultimaISO = fechasISO.length ? fechasISO[fechasISO.length - 1] : null;

            const sesiones = fechasISO.map(iso => ({
                iso,
                label:     this.formatFecha(iso),
                // Bloqueada si NO es la más reciente
                bloqueada: iso !== ultimaISO,
            }));

            // 5. Mapa (insc_id, fecha_iso) → { asistencia_id, presente }
            const mapa = {};
            for (const r of records) {
                const fISO = toISO(r.fecha);
                const inscId = Array.isArray(r.inscripcion_id)
                    ? r.inscripcion_id[0]
                    : r.inscripcion_id;
                mapa[`${inscId}_${fISO}`] = {
                    asistencia_id: r.id,
                    presente:      r.presente,
                };
            }

            // 6. Inscripciones ordenadas alfabéticamente
            const inscIds = actividad.inscripcion_ids || [];
            const inscripciones = inscIds.length
                ? await this.orm.read("actividad.inscripcion", inscIds, ["id", "partner_id"])
                : [];
            inscripciones.sort((a, b) =>
                (a.partner_id[1] || "").localeCompare(b.partner_id[1] || "")
            );

            // 7. Construir filas
            const filas = inscripciones.map(insc => {
                const celdas = {};
                for (const ses of sesiones) {
                    celdas[ses.iso] = mapa[`${insc.id}_${ses.iso}`]
                                   || { asistencia_id: null, presente: false };
                }
                return {
                    partner_id: insc.partner_id[0],
                    insc_id:    insc.id,
                    nombre:     insc.partner_id[1] || "(Sin nombre)",
                    celdas,
                };
            });

            this.state.sesiones = sesiones;
            this.state.filas    = filas;
            this.state.readonly = readonly;

        } catch (e) {
            console.error("PaseListaPivot.loadData error:", e);
        } finally {
            this.state.loading = false;
        }
    }

    async reload() { await this.loadData(); }

    // ── Exportar Excel ────────────────────────────────────────────────
    async exportarExcel() {
        const aid = this.actividadId;
        if (!aid || this.state.exportando) return;
        this.state.exportando = true;
        try {
            const resp = await fetch(`/actividades/pase-lista/${aid}/exportar-excel`, {
                method: "GET",
                credentials: "include",
                headers: { "X-Requested-With": "XMLHttpRequest" },
            });
            if (!resp.ok) {
                const txt = await resp.text().catch(() => "");
                throw new Error(`HTTP ${resp.status}: ${txt.slice(0, 200)}`);
            }
            const contentType = resp.headers.get("Content-Type") || "";
            if (!contentType.includes("spreadsheet") && !contentType.includes("octet")) {
                const txt = await resp.text().catch(() => "");
                throw new Error(`Respuesta inesperada: ${txt.slice(0, 200)}`);
            }
            const disposition = resp.headers.get("Content-Disposition") || "";
            const match = disposition.match(/filename[^;=\n]*=["'\']?([^"\'\';\n]+)/);
            const filename = match ? match[1].trim() : `actividad_${aid}_lista.xlsx`;
            const blob = await resp.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => URL.revokeObjectURL(url), 1000);
            this.showToast("Excel descargado ✓", true);
        } catch (e) {
            console.error("exportarExcel error:", e);
            this.showToast(`Error: ${e.message || "Intente de nuevo."}`, false);
        } finally {
            setTimeout(() => { this.state.exportando = false; }, 2500);
        }
    }

    // ── Toggle — solo actúa en la sesión más reciente ─────────────────────
    async onToggle(ev, fila, iso) {
        // Verificación defensiva: rechazar si la sesión está bloqueada
        const ses = this.state.sesiones.find(s => s.iso === iso);
        if (!ses || ses.bloqueada || this.state.readonly) {
            ev.preventDefault();
            ev.target.checked = !ev.target.checked;  // revertir
            this.showToast("Esta sesión ya está cerrada y no puede modificarse.", false);
            return;
        }

        const nuevoValor = ev.target.checked;
        const celda = fila.celdas[iso];
        if (!celda?.asistencia_id) return;

        celda.presente = nuevoValor;   // optimistic UI

        try {
            await this.orm.write(
                "actividad.asistencia",
                [celda.asistencia_id],
                { presente: nuevoValor }
            );
            this.showToast("Guardado ✓", true);
        } catch (err) {
            // Revertir en caso de error del servidor
            celda.presente    = !nuevoValor;
            ev.target.checked = !nuevoValor;
            const msg = err?.data?.message || err?.message || "Error al guardar";
            this.showToast(msg, false);
        }
    }

    // ── Helpers de conteo ─────────────────────────────────────────────────
    contarFila(fila) {
        return this.state.sesiones.filter(s => fila.celdas[s.iso]?.presente).length;
    }

    contarCol(iso) {
        return this.state.filas.filter(f => f.celdas[iso]?.presente).length;
    }

    // ── Formatea "YYYY-MM-DD" → "19 may" ──────────────────────────────────
    formatFecha(iso) {
        const [, m, d] = iso.split("-");
        const meses = ["ene","feb","mar","abr","may","jun",
                       "jul","ago","sep","oct","nov","dic"];
        return `${parseInt(d, 10)} ${meses[parseInt(m, 10) - 1]}`;
    }

    showToast(msg, ok) {
        this.state.toast = { msg, ok };
        clearTimeout(this._toastTimer);
        this._toastTimer = setTimeout(() => {
            this.state.toast = { msg: "", ok: true };
        }, 3000);
    }
}

registry.category("actions").add("pase_lista_pivot_action", PaseListaPivot);
