FROM odoo:19

USER root

COPY ./custom_addons 
COPY ./docker/odoo.conf /etc/odoo/odoo.conf
CMD ["odoo", "-i", "base", "--without-demo=all"]
USER odoo
