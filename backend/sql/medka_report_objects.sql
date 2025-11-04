DROP VIEW IF EXISTS v_billing_data CASCADE;


CREATE OR REPLACE VIEW v_billing_data AS
WITH matched AS (
    select
        bi.id AS invoice_id,
        bi.invoice_number,
        bi.invoice_date,
        bi.online_szamla_status,
        bi.cancelled,
        bi."type",
        bii.id AS item_id,
        bii.name,
        bii.net_amount,
        p.product_value,
        p.product_description,
        p.purchase_price_huf,
        p.uom,
        p.uom_hun,
        p.cap_disp,
        LENGTH(p.product_value) AS match_len,
        ROW_NUMBER() OVER (
            PARTITION BY bii.id
            ORDER BY LENGTH(p.product_value) DESC
        ) AS rn
    FROM bank_transfers_billingoinvoice bi
    INNER JOIN bank_transfers_billingoinvoiceitem bii 
        ON bi.id = bii.invoice_id
    LEFT JOIN bank_transfers_productprice p 
        ON bii.name LIKE p.product_value || '%' and bi.fulfillment_date between p.valid_from and coalesce(p.valid_to , '9999-12-31')
        where type != 'draft' 
          and not exists (select 1 from bank_transfers_billingorelateddocument br 
          								 WHERE br.invoice_id = bi.id 
       												OR br.related_invoice_id = bi.id)
)
select
    invoice_id,
    invoice_number,
    invoice_date,
    online_szamla_status,
    cancelled,
    "type",
    item_id,
    name,
    product_value,
    product_description,
    uom,
    uom_hun,
    cap_disp
FROM matched
WHERE rn = 1;

DROP VIEW IF EXISTS v_supplier_with_cat_and_type CASCADE;


CREATE OR REPLACE VIEW v_supplier_with_cat_and_type AS
select bts.id, bts.partner_name, sc."name" cat_name, bt."name" type_name, bts.valid_from , coalesce(bts.valid_to, '9999-12-31') valid_to
from bank_transfers_supplier bts 
				 left outer join bank_transfers_suppliercategory sc on  bts.category_id = sc.id and sc.company_id = 3 and bts.company_id = 3
		     left outer join bank_transfers_suppliertype bt on bts.type_id = bt.id and bt.company_id = 3; 


DROP VIEW IF EXISTS v_costs CASCADE;

CREATE OR REPLACE VIEW v_costs AS
select bs.id, bs.category, bs.paid_at, bs.fulfillment_date, 
       bs.invoice_number , bs.currency , bs.conversion_rate , 
       bs.total_gross , bs.total_gross_local , 
       bs.total_vat_amount, bs.total_vat_amount_local , 
       bs.invoice_date , bs.due_date , bs.payment_method, 
       bs."comment" description, 
       bs.partner_name , bs.partner_tax_code , 
       s.cat_name, s.type_name, s.valid_from, s.valid_to
from bank_transfers_billingospending bs 
    left outer join v_supplier_with_cat_and_type s on bs.partner_name = s.partner_name and bs.invoice_date  between s.valid_from and s.valid_to and bs.company_id =3 
UNION
select bt.id, 'other' category, null paid_at, bt.booking_date fulfillment_date, 
       null invoice_number, bt.currency , null conversion_rate,  
       -1*bt.amount total_gross, -1*bt.amount total_gross_local, 
       null total_vat_amount, null total_vat_amount_local, 
       bt.booking_date invoice_date, bt.booking_date due_date, 'wire_transfer' payment_method ,
       bt.short_description description, 
       bs.bank_name, null partner_tax_code , 
       s.cat_name , s.type_name , s.valid_from , s.valid_to 
  from bank_transfers_banktransaction bt 
        inner join bank_transfers_bankstatement bs on  bs.id = bt.bank_statement_id  and bs.company_id  = 3
        inner join v_supplier_with_cat_and_type s on bt.booking_date between s.valid_from and s.valid_to and s.partner_name ='Költségelszámolás'
where bt.transaction_type = 'BANK_FEE' 
union 
select bt.id, 'other' category, null paid_at, bt.booking_date fulfillment_date, 
       null invoice_number, bt.currency , null conversion_rate,  
       -1*bt.amount total_gross, -1*bt.amount total_gross_local, 
       null total_vat_amount, null total_vat_amount_local, 
       bt.booking_date invoice_date, bt.booking_date due_date, 'wire_transfer' payment_method ,
       bt.short_description description, 
       bs.bank_name, null partner_tax_code ,
       s.cat_name , s.type_name , s.valid_from , s.valid_to 
  from bank_transfers_banktransaction bt 
        inner join bank_transfers_bankstatement bs on  bs.id = bt.bank_statement_id  and bs.company_id  = 3
        left outer join v_supplier_with_cat_and_type s on bt.booking_date between s.valid_from and s.valid_to and bt.beneficiary_name = s.partner_name 
where bt.beneficiary_name in ('Kövesi Dániel', 'Fekete Dávid') or bt.beneficiary_name like '%NAV%'
; 

GRANT SELECT ON v_costs to medka_reader;
GRANT SELECT ON v_supplier_with_cat_and_type to medka_reader;
GRANT SELECT ON v_billing_data to medka_reader;

