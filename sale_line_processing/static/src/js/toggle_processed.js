/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";

function applyProcessedFilter() {
    const body = document.body;
    const table = document.querySelector('.o_field_x2many_list_view table.o_list_table');
    if (!table) return;

    const hide = body.classList.contains('o_hide_processed');
    table.querySelectorAll('tr.o_data_row').forEach(tr => {
        const checkbox = tr.querySelector('td[data-name="processed"] input[type="checkbox"]');
        if (checkbox && checkbox.checked && hide) {
            tr.style.display = 'none';
        } else {
            tr.style.display = '';
        }
    });
}

function createToggle() {
    // Jos nappi on jo olemassa, ei lisätä toista
    if (document.querySelector('.o_toggle_processed_checkbox')) return;

    const tryInsert = () => {
        // Etsitään Tilausrivit-taulukko mahdollisimman monipuolisesti
        const orderLineField =
            document.querySelector('.o_field_x2many_list_view') ||
            document.querySelector('.o_field_one2many') ||
            document.querySelector('.o_list_view');

        if (orderLineField) {
            // Luo checkbox-elementti
            const div = document.createElement('div');
            div.innerHTML = `
                <label style="display:flex;align-items:center;gap:8px;margin:6px 0 10px 0;font-weight:500;">
                    <input type="checkbox" class="o_toggle_processed_checkbox" checked>
                    <span>Näytä käsitellyt rivit</span>
                </label>
            `;

            // Lisää se ennen rivitaulukkoa
            orderLineField.parentElement.insertBefore(div, orderLineField);

            // Lisää logiikka
            const checkbox = div.querySelector('input');
            checkbox.addEventListener('change', () => {
                document.body.classList.toggle('o_hide_processed', !checkbox.checked);
                applyProcessedFilter();
            });

            // Tarkkaile DOMia (jos rivejä lisätään)
            const observer = new MutationObserver(applyProcessedFilter);
            observer.observe(orderLineField, { childList: true, subtree: true });

            applyProcessedFilter();
            return true;
        }
        return false;
    };

    // Odotetaan kunnes taulukko on luotu
    const interval = setInterval(() => {
        if (tryInsert()) clearInterval(interval);
    }, 500);
}


// Patchataan FormController vain myyntitilaukselle
patch(FormController.prototype, {
    setup() {
        super.setup();

        // Odotetaan hetki, että näkymä on latautunut
        setTimeout(() => {
            // Tarkistetaan että ollaan "sale.order" -mallissa
            const model = this.model?.root?.resModel || this.props?.resModel;
            if (model === "sale.order") {
                createToggle();
            }
        }, 800);
    },
});

