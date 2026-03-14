FROM odoo:19

USER root

RUN mkdir -p /mnt/custom-addons
COPY custom_addons /mnt/custom-addons
COPY docker/odoo.conf /etc/odoo/odoo.conf

USER odoo

CMD ["odoo"]
