/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    async beforeLeave() {
        if (
            this.model.root.isDirty &&
            this.model.root.resModel === "actividad.empleado.permiso"
        ) {
            const guardar = window.confirm(
                "¿Desea guardar los cambios antes de salir?"
            );
            if (guardar) {
                await this.model.root.save();
            } else {
                this.model.root.discard();
            }
            return true;
        }
        return super.beforeLeave?.();
    },
});