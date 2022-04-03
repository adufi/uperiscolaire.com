function macro_innerHTML (e, innerHTML) {
    document.querySelectorAll(e).forEach((item) => { item.innerHTML = innerHTML; });
}

function getVadsLink (pid, pmail, amount, cart) {
    /**
        
        @params pid=20,p=1001[20,21],p=1002[20,21],p=1002[20,21],p=1002[20,21],p=1002[20,21],
    */
    let formated_cart = '';
    for (const _ of cart) {
        formated_cart += `!p=${_.product},${_.children.join(',')}`;
    }

    return `https://paiement.systempay.fr/vads-site/UNION_DES_PARENTS_D__ELEVES_ET?lck_vads_amount=${amount}&lck_vads_cust_email=${pmail}&lck_vads_ext_info_Informations=?v=1!pid=${pid}${formated_cart}`;
    return `https://paiement.systempay.fr/vads-site/UNION_DES_PARENTS_D__ELEVES_ET?ctx_mode=TEST&lck_vads_amount=${amount}&lck_vads_cust_email=${pmail}&lck_vads_ext_info_Param%C3%A8tres=?v=1!pid=${pid}${formated_cart}&lck_vads_ext_info_Informations=?v=1!pid=${pid}${formated_cart}`;
}

/** NOTES
 *  Products
 *  - Normal
 *  - Normal (without icon and stock)    
 *  - Selected
 *  - Reserved
 *  - Bought
 *  - Summary OK
 *  - Summary Ban 
 *  + PERI (remove stock)
 * 
 */

const _Product = {
    
    create ({
        id = '',
        type = 'normal',
        className = '',
        attributes = {},

        name = '',

        stock_max = 0,
        stock_current = 0,

        date = '',
        price = 0,
        
    } = {}) {
        const div = document.createElement('div');

        div.id = id;
        div.className = `product-tile ${type} ${className}`;

        Object.keys(attributes).forEach(key => div.setAttribute(key, attributes[key]));

        div.innerHTML = `
        <div class="header">
            <div class="name">${name}</div>
            <div class="stock">Places: ${Math.max(stock_max - stock_current, 0)}</div>
        </div>
    
        <div class="body">
            <div class="icon add"><i class="fas fa-plus"></i></div>
            <div class="icon ban"><i class="fas fa-ban"></i></div>
            <div class="icon check"><i class="fas fa-check"></i></div>
            <div class="icon selected"><i class="fas fa-cart-arrow-down"></i></div>
            <div class="icon expired"><i class="icon calendar times outline"></i></div>
            <div class="icon empty"><i class="icon exclamation circle"></i></div>
            <div class="icon checkbox"><input type="checkbox" onclick=""/></div>
        </div>
    
        <div class="footer">
            <div class="price"><span class="price__amount">${price}</span> €</div>
            <div class="date">payé le <span class="date__date">${date}</span></div>
        </div>`;

        return div;
    },

    getPrice (intel, product) {
        let price = product.price;
        let quotient = 0;
    
        const categories_q1 = [10, 11, 12, 13, 14, 15];
    
        if (product.category !== 0 && product.category !== 1) {
            if (categories_q1.includes(product.category)) {
                quotient = intel.quotient_1;
            }
            else {
                quotient = intel.quotient_2;
            }
        }
    
        if (quotient === 2) {
            price = product.price_q2;
        }
        else if (quotient === 3) {
            price = product.price_q1;
        }
    
        return price;
    }
};


class Shop {
    /**     HTML Struct
     *      #Shop
     *          .Controls
     *          .Dir-Intels
     *              .Intels
     *              .Dir
     *          .Children-Records
     *          .View
     *              .ChildView
     *                  .Filters
     *                      .Period
     *                      .Category
     *                  .Products
     *                      .ProductCategory
     *                          .product-tile              
     */




    constructor () {
        this._mode = 0;

        this._products = [];
        this._raw_products = [];

        this._active_school_year = {};

        this._caster = {};
        this._parent = {};
        this._children = [];

        this._localOrder = {};

        // From inputs
        this._ref = '';
        this._type = 1;
        this._comment = '';

        this._amount = 0;
        this._selectedProducts = 0;

        this._cart = [];

        // To continue
        this.child_id = 0;

        // Errors
        this._has_errors = false;
        this._error_msg = '';
    }

    setCaster (caster) { this._caster = caster; }
    setModeView (mode) { this._mode = mode; }
    setActiveSchoolYear (sy) { this._active_school_year = sy; }

    setProducts (raw) {
        this._raw_products = raw;

        // Convert product category (int) to this._products keys
        const KEYS = [
            'UNSET',
            'PERISCOLAIRE',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'AVRIL',
            'MAI',
            'JUIN',
            'JUILLET',
            'AOUT',
            'SEPTEMBRE',
            'OCTOBRE',
            'NOVEMBRE',
            'DECEMBRE',
            'TOUSSAINT',
            'NOEL',
            'CARNAVAL',
            'PAQUES',
            'GRDS_VACANCES_JUILLET',
            'GRDS_VACANCES_AOUT'
        ];

        this._products = {
            'AUCUNE CATEGORIE': [],
            'PERISCOLAIRE': [],
            'SEPTEMBRE':    [],
            'OCTOBRE':  [],
            'TOUSSAINT':    [],
            'NOVEMBRE': [],
            'DECEMBRE': [],
            'NOEL': [],
            'JANVIER':  [],
            'FEVRIER':  [],
            'MARS': [],
            'CARNAVAL': [],
            'AVRIL':    [],
            'PAQUES':   [],
            'MAI':  [],
            'JUIN': [],
            'JUILLET':  [],
            'GRDS_VACANCES_JUILLET':   [],
            'AOUT': [],
            'GRDS_VACANCES_AOUT':  [],
        };

        for (const p of raw) {
            const key = KEYS[p.category];

            this._products[key].push(p);
        }

        // POST TREATMENT
        for (const category of Object.keys(this._products)) {
            if (category === 'PERISCOLAIRE') {
                this._products[category].sort(function (a, b) {
                    return a.order - b.order;
                });
            }
            else {
                this._products[category].sort(function (a, b) {
                    return a.date - b.date;
                });
            }
        }
    }    

    setParent (parent, intels, client) {
        // Release 1.5.3
        return;

        this._parent = parent;
        this._parent.orders = [];

        if (client || Object.keys(client).length) {
            this._parent['client'] = client;
        }
        else {
            this._parent['client'] = {'credit': 0};
        }

        for (const intel of intels) {
            if (intel.school_year === this._active_school_year.id) {
                this._parent.intel = intel;
                return;       
            }
        }

        this._parent.intel.quotient_1 = 0;
        this._parent.intel.quotient_2 = 0;
        this._parent.intel.recipent_number = 0;
    }

    setChildren (children, records) {
        // Release 1.5.3
        return;

        if (children && children.length) {
            for (const child of children) {
                const _ = child;
                _.record = {};
                _.tickets = {};
    
                for (const record of records) {
                    if ((child.id === record.child) &&
                    (record.school_year === this._active_school_year.id)) {
                        _.record = record;
                        break;       
                    }
                }
    
                this._children.push(_);
            }
        }
        else {
            this._has_errors = true;
            this._error_msg = 'Aucun enfant trouvé.';
        }
        
    }

    // Set parent orders
    setOrders (orders) {
        // Release 1.5.3
        return;
        
        this._orders = orders;

        const children_tickets = {};

        // Date are ordered in descending order (newest first)
        // Reverse loop to bypass this issue
        for (let i = orders.length - 1; i >= 0; --i) {
            const o = orders[i];

            const order = {
                id: o.id,
                date: o.date,
                amount: o.amount,
            };

            for (const t of o.tickets) {

                const ticket = {
                    id: t.id,
                    payee: t.payee,
                    price: t.price,
                    product: t.product,

                    date: undefined,
                    status: undefined,

                    order: this._orders.length,
                };

                if (t.hasOwnProperty('status')) {
                    if (t.status.length) {
                        ticket.date = App.Utils.dateTimeToHTML(t.status[0].date);
                        ticket.status = t.status[0].status;
                    }
                }

                if (!children_tickets.hasOwnProperty(t.payee)) {
                    children_tickets[t.payee] = {};
                }

                children_tickets[t.payee][t.product] = ticket;
            }

            this._parent.orders.push(order);
        }

        // Bind tickets to child
        this._children.forEach(child => {
            if (children_tickets.hasOwnProperty(child.id)) {

                child.tickets = children_tickets[child.id];
            }
        });
    }

    // Release 1.5.3

    setParent_v2 (parent) {
        this._parent = parent;
        this._parent.orders = [];

        if (parent.hasOwnProperty('client') && parent.client.hasOwnProperty('credit')) {
            this._parent['client'] = parent.client;
        }
        else {
            this._parent['client'] = {'credit': 0};
        }

        // Intels
        if (!Object.keys(parent.intel).length) {
            this._parent.intel.quotient_1 = 0;
            this._parent.intel.quotient_2 = 0;
            this._parent.intel.recipent_number = 0;
        }

        this.child_id = parent.id;
    } 

    setChildren_v2 (children) {
        if (children && children.length) {
            for (const child of children) {
                child.tickets = {};
                this._children.push(child);
            }
        }
        else {
            this._has_errors = true;
            this._error_msg = 'Aucun enfant trouvé.';
        }   
    }

    setOrders_v2 (orders) {
        const children_tickets = {};

        // Date are ordered in descending order (newest first)
        // Reverse loop to bypass this issue
        // for (let i = orders.length - 1; i >= 0; --i) {
            // const o = orders[i];
        for (let i = 0; i < orders.length; ++i) {
            const o = orders[i];

            const order = {
                id: o.id,
                date: o.date,
                amount: o.amount,
            };

            for (const t of o.tickets) {

                const ticket = {
                    id: t.id,
                    payee: t.payee,
                    price: t.price,
                    product: t.product,

                    date: undefined,
                    status: undefined,

                    order: i,
                };

                if (t.hasOwnProperty('status')) {
                    if (t.status.length) {
                        ticket.date = App.Utils.dateTimeToHTML(t.status[0].date);
                        ticket.status = t.status[0].status;
                    }
                }

                if (!children_tickets.hasOwnProperty(t.payee)) {
                    children_tickets[t.payee] = {};
                }

                children_tickets[t.payee][t.product] = ticket;
            }

            this._parent.orders.push(order);
        }

        // Bind tickets to child
        this._children.forEach(child => {
            if (children_tickets.hasOwnProperty(child.id)) {

                child.tickets = children_tickets[child.id];
            }
        });
    }

    // set order save in local storage
    setLocalOrder (order) {
        try {
            // Check order integrity (caster/parent)
            if (order.caster !== this._caster.id) {
                Messages().warning.write('toLocalStorage', 'Sauvegarde incorrect (emetteur). Création d\'un nouveau panier.');
                return false;
            }
            if (order.payer !== this._parent.id) {
                Messages().warning.write('toLocalStorage', 'Sauvegarde incorrect (parent). Création d\'un nouveau panier.');
                return false;
            }
    
            // Type verification
            if (order.reference) {
                this._ref = order.reference;
                
                if (!order.type) {
                    Messages().warning.write('type', 'Aucun type de reçu pour la référence.');
                }
                else {
                    if (order < 1 || order > 8) {
                        Messages().error.write('type', 'Type de reçu invalide.');
                    }
                    else {
                        this._type = order.type;
                    }
                }
            }

            // Hotfix 1.5.4
            this._cart = [];

            // Add cart to children tickets
            // Check tickets errors
            let errorProducts = 0, selectedProducts = 0;
            for (const item of order.cart) {
                // item { product: <id>, children: [<id>] }
                for (const id of item.children) {

                    // Look for child
                    for (const child of this._children) {

                        if (id === child.id) {
                            if (child.tickets.hasOwnProperty(item.product)) {
                                // Error product is present
                                errorProducts += 1;

                            }
                            else {
                                selectedProducts += 1;
                                child.tickets[item.product] = {
                                    'status': -1
                                };

                                this._cart.push(item);
                            }
                            break;
                        }
                    }
                }
            }
            
            // Hotfix 1.5.4
            if (errorProducts) {
                if (errorProducts == 1) {
                    Messages().warning.write('errorProducts', `1 produit a été retiré du panier, car il n'est plus valide.`);
                }
                else {
                    Messages().warning.write('errorProducts', `${errorProducts} produits ont été retirés du panier, car ils ne sont plus valides.`);
                }
                
                // Messages().warning.write('errorProducts', `Les produits ont été retirés du panier, car ils ne sont plus valides.`);
            }
            // End hotfix

            this._amount = order.amount;
            this._comment = order.comment;
            this._selectedProducts = selectedProducts;
            
            this._localOrder = order;
            
            return true;
        }
        catch (e) {
            console.error(e);
            return false;
        }
    }

    // Render & UI
    //

    ready () {
        $('.ui.dropdown').dropdown({transition: 'drop', on: 'click' });
    }

    render_ModeView () {

        switch (this._mode) {

            // Shop mode
            case 1: {
                this.render_Controls();
                this.render_Intels();
                if (App.caster.isAdmin)
                    this.render_Dir();
                this.render_Children();
                this.render_Records();
                this.render_View();
                this.ready();
                
                break;
            }
            
            // View mode
            case 2: {
                this.render_Intels();
                this.render_Children();
                this.render_Records();
                this.render_View();
                this.ready();

                break;
            }

            default: {
                Messages().error.write('shop', 'Aucun mode d\'affichage sélectionné.');
                break;
            }
        }
    }

    // Render Controls
    render_Controls () {
        document.querySelector('#Shop .Controls').classList.remove('d-none');

        document.querySelector('#Shop .Controls .Controls-buttons .controls-amount').innerHTML = this._amount;
        document.querySelector('#Shop .Controls .Controls-texts .controls-items_selected').innerHTML = this._selectedProducts;
        
        document.querySelector('#Shop .Controls .controls-cancel').onclick = (e) => this.onButtonCancelClick(e);
        document.querySelector('#Shop .Controls .controls-previous').onclick = (e) => this.onButtonPreviousClick(e);
        document.querySelector('#Shop .Controls .controls-continue').onclick = (e) => this.onButtonContinueClick(e);
    }
    
    // Render Intels (Caster/Parent/Credit)
    render_Intels () {
        document.querySelector('#Shop .Dir-Intels .Intels').classList.remove('d-none');

        // Caster
        macro_innerHTML('.Intels-caster .Intels__first_name', this._caster.first_name);
        macro_innerHTML('.Intels-caster .Intels__last_name', this._caster.last_name);

        // Parent
        macro_innerHTML('.Intels-parent .Intels__first_name', this._parent.first_name);
        macro_innerHTML('.Intels-parent .Intels__last_name', this._parent.last_name);
        
        // Parent email
        if (this._parent.hasOwnProperty('email')) {

            macro_innerHTML('.Intels-parent .Intels__email', this._parent.email);
        }
        else if (this._parent.hasOwnProperty('auth') 
            && this._parent.auth.hasOwnProperty('email'))
            macro_innerHTML('.Intels-parent .Intels__email', this._parent.auth.email);
        else
            macro_innerHTML('.Intels__email', '<i>Pas d\'email.</i>');

        // Parent credit
        if (this._parent.hasOwnProperty('client') &&
            this._parent.client.hasOwnProperty('credit')) {

            macro_innerHTML('.Intels-credit .Intels__credit', this._parent.client.credit);
        }
    }

    // Render Dir (Order Ref/Type)
    render_Dir () {
        document.querySelector('#Shop .Dir-Intels .Dir').classList.remove('d-none');

        document.querySelector('#Shop .Dir-Intels .Dir input[name="shop[ref]"]').value = this._ref;
        document.querySelector('#Shop .Dir-Intels .Dir input[name="shop[ref]"]').onchange = (e) => this.onRefChanged(e);

        const etype = document.querySelector('#Shop .Dir-Intels .Dir input[name="shop[type]"]');
        if (this._type > 1) {
            const v = etype.parentElement.querySelector(`.item[data-value="${this._type}"]`).innerHTML;
            const dt = etype.parentElement.querySelector('.default.text');
            dt.classList.remove('default');
            dt.innerHTML = v;
            etype.value = this._type;
        }
        etype.onchange = (e) => this.onTypeChanged(e);

        document.querySelector('#Shop .Dir-Intels .Dir textarea[name="shop[comment]"]').value = this._comment;
        document.querySelector('#Shop .Dir-Intels .Dir textarea[name="shop[comment]"]').onchange = (e) => this.onCommentChanged(e);
    }

    // Render Children label
    render_Children () {
        document.querySelector('#Shop .Children-Records .Children').classList.remove('d-none');

        const content = document.querySelector('#Shop .Children-Records .Children .content');
        
        for (const child of this._children) {
            const div = document.createElement('div');
            div.className = 'ui big label';
            div.innerHTML = child.first_name;
            div.setAttribute('data-child', child.id);

            div.onclick = (e) => this.onChildLabelClick(e);
            
            content.appendChild(div);
        }
    }
    
    // Render Children records
    render_Records () {
        document.querySelector('#Shop .Children-Records .Records').classList.remove('d-none');

        const content = document.querySelector('#Shop .Children-Records .Records .content');
        
        const s = this._active_school_year.date_start.split('-')[0];
        const e = this._active_school_year.date_end.split('-')[0];

        for (const child of this._children) {
            if (Object.keys(child.record).length) {

                const school = (child.record['school']) ? child.record['school'] : '<i>pas d\'école renseignée</i>'
                const classroom = CLASSROOMS[child.record['classroom']];
                const quotient_2 = QUOTIENT[this._parent.intel['quotient_2']];
                const quotient_1 = QUOTIENT[this._parent.intel['quotient_1']];
    
                content.innerHTML += `
                <div class="card" data-child="${child.id}">
                    <div><b>Ecole: </b>          <span class="record-school">        ${school}</span></div>
                    <div><b>Classe: </b>         <span class="record-classroom">     ${classroom}</span></div>
                    <div><b>Quotient ${s}: </b>  <span class="record-quotient-q1">   ${quotient_1}</span></div>
                    <div><b>Quotient ${e}: </b>  <span class="record-quotient-q2">   ${quotient_2}</span></div>
                </div>`;
            }
            else {
                Messages().warning.write('inscription', `Aucune inscription pour ${child.first_name} ${child.last_name}`);

                content.innerHTML += `
                <div class="card" data-child="${child.id}">
                    <div class="text-danger"><b>Aucune inscription pour cette année.</b></div>
                </div>`;
            }
        }
    }

    // Render Children Tabs
    render_View () {
        document.querySelector('#Shop .View').classList.remove('d-none');

        const content = document.querySelector('.View .content');

        for (const child of this._children) {
            let div = document.createElement('div');
                div.className = 'ChildView ' + ((false) ? 'active' : '');
                div.setAttribute('data-child', child.id);

            content.appendChild(div);

            // Wrapper
            let wrapper = document.createElement('div');
                wrapper.className = 'wrapper';
                    
            div.appendChild(wrapper);

            // Wrapper title & title
            let title = document.createElement('p');
                title.className = 'title';
                title.innerHTML = `${child['first_name']} ${child['last_name']}`;

            let wrapper_title = document.createElement('div');
                wrapper_title.className = 'wrapper-title';
                wrapper_title.appendChild(title);
            
            wrapper.appendChild(wrapper_title);

            // Wrapper content
            let wrapper_content = document.createElement('div');
                wrapper_content.className = 'wrapper-content';
            
                wrapper.appendChild(wrapper_content);

            if (Object.keys(child.record).length) {
                // Is MAT or ELE
                const sub = (child.record['classroom'] > 0 && child.record['classroom'] < 5) ? 1 : 2;
    
                this._render_ViewContent(wrapper_content, sub, child.tickets);
            }
            else {
                this._render_ViewNoContent(wrapper_content);
            }
        }
    }

    // Render Filters (see _render_ViewFilters) + Categories + Products
    _render_ViewContent (container, sub, tickets) {
        /**
         *  container
         *      Filters
         *          Base
         *          Category
         *      Products    
         * 
         * 
         * 
         */

        // <div class="Filters">
        //             <div class="built-in">

        //             </div>

        //         </div>

        //         <div class="Products">
        //             <div class="content"></div>
        //         </div>

        const filters = document.createElement('div');
        filters.className = 'Filters';
        container.appendChild(filters);

        // Period inside Filters
        const periods = document.createElement('div');
        periods.className = 'Period';
        filters.appendChild(periods);

        // Render Filters
        this._render_ViewFilters(periods);

        // Category inside Filters
        const tags = document.createElement('div');
        tags.className = 'Category d-none';
        filters.appendChild(tags);

        const products = document.createElement('div');
        products.className = 'Products';
        container.appendChild(products);

        let today = new Date();

        // Loop through products
        for (const key of Object.keys(this._products)) {

            // Check if there is products in category
            if (!this._products[key].length) continue;

            // Create product CONTENT
            const content = document.createElement('div');
            content.className = 'content';

            // Create content MAIN TILE
            if (this._mode === 1) {

                const main = _Product.create({
                    type: 'main',
    
                    name: 'Tout cocher',
                    attributes: { 'data-category': key },
                });
    
                main.onclick = (e) => this.onMainProductTileClick(e);
    
                content.appendChild(main);
            }

            // Has bought at least one product
            let oneProduct = false;

            // Create content PRODUCTS
            for (const product of this._products[key]) {

                // Render products bought
                if (tickets.hasOwnProperty(product.id)) {
                    const ticket = tickets[product.id];

                    const REF = [
                        undefined,
                        'reserved',
                        'purchased',
                    ];

                    oneProduct = true;

                    if (REF[ticket.status]) {
                        const isFloat = (ticket.price !== Math.round(ticket.price)) ? true : false;
                        const price = (typeof(ticket.price) === 'number' && isFloat) ? ticket.price.toPrecision(4) : ticket.price;
                        content.appendChild(
                            _Product.create({
                                type: REF[ticket.status],

                                name: product.name,
                                attributes: {
                                    'data-product': product.id,
                                    'data-category': key
                                },
                                stock_max: product.stock_max,
                                stock_current: product.stock_current,
        
                                date: ticket.date,
                                price: price
                            })
                        );
                        continue;
                    }
                    else if (ticket.status === -1) {
                        const _ = _Product.create({
                            type: 'selected',

                            name: product.name,
                            attributes: {
                                'data-product': product.id,
                                'data-category': key
                            },
                            stock_max: product.stock_max,
                            stock_current: product.stock_current,
    
                            price: _Product.getPrice(this._parent.intel, product)
                        })
                        _.onclick = (e) => this.onProductTileClick(e);
                        content.appendChild(_);
                        continue;
                    }
                }

                
                // Render other products only if:
                //  Mode is in SHOP
                //  Product is ACTIVE
                if (this._mode === 1 && product.active) {
                    if (product.category === 1 || product.subcategory === sub) {
                        
                        let type = 'normal';

                        if (product.stock_max != 0 && ((product.stock_max - product.stock_current) < 0)) {
                            type = 'empty';
                        }

                        if (product.date_end) {
                            const d = new Date(product.date_end);

                            if (d.getTime() !== NaN) {
                                if (today > d) {
                                    type = 'expired';
                                }
                            }
                        }

                        const _ = _Product.create({
                            type: type,
                            
                            name: product.name,
                            attributes: {
                                'data-product': product.id,
                                'data-category': key
                            },
                            stock_max: product.stock_max,
                            stock_current: product.stock_current,
                            
                            // date: ticket.date,
                            price: _Product.getPrice(this._parent.intel, product)
                        });
                        
                        _.onclick = (e) => this.onProductTileClick(e);

                        content.appendChild(_);
                        
                        // const _ = productHelper.createFromProduct('normal', product, this._parent.intel)
                        // _.setAttribute('data-category', key);
                        
                        // products.appendChild(_);
                    }
                }
            }

            // Render ProductCategory only if:
            //  Mode is in SHOP
            //  At least one product have been bought
            if (oneProduct || this._mode === 1) {

                const sp = {
                    GRDS_VACANCES_JUILLET: 'GRDS VACANCES JUILLET',
                    GRDS_VACANCES_AOUT: 'GRDS VACANCES AOUT',
                };

                const h5_title = (sp[key]) ? sp[key] : key;

                // Filter Category
                tags.innerHTML += `<div class="ui large label" data-category="${key}">${key}</div>`;
    
                // ProductCategory
                const productcategory = document.createElement('div');
                productcategory.className = 'ProductCategory ' + key;
                products.appendChild(productcategory);
    
                // Title
                const h5 = document.createElement('h5');
                h5.innerHTML = h5_title;
                productcategory.appendChild(h5);
    
                // Append ProductCategory - Definition up there
                productcategory.appendChild(content);
            }
        };

        // document
        // .querySelectorAll('#Shop .View .ChildView .Filters .ui.label')
        // .forEach(label => label.onclick = (e) => this.onCategoryClick(e));

        for (const tag of tags.children) tag.onclick = (e) => this.onCategoryClick(e);
        for (const period of periods.children) period.onclick = (e) => this.onPeriodClick(e);


        // Moved in main code
        // 
        // this.setActiveCategory('PERISCOLAIRE');
        // this.setCategoriesByMonth(new Date().getMonth());

        return;
    }

    // Render Filters
    _render_ViewFilters (container) {
        if (true || App.caster.isAdmin) {
            container.innerHTML += `
                <div class="ui large label" data-category="GARDERIE">GARDERIE</div>
                <div class="ui large label" data-category="MERCREDIS">MERCREDIS</div>
                <div class="ui large label" data-category="VACANCES">VACANCES</div>`;
        }
        else {
            container.innerHTML += `
                <div class="ui large label" data-category="GARDERIE">GARDERIE</div>`;
        }
    }

    // Render an error message in View content
    _render_ViewNoContent (container) {
        container.innerHTML = `<div class="text-danger"><b>Aucune inscription pour cette année.</b></div>`;
    }


    // LOGICS
    //

    setSelectedProducts (n) {
        this._selectedProducts = n;
        document.querySelector('#Shop .Controls .Controls-texts .controls-items_selected').innerHTML = n;
    }
    
    setAmount (amount) {
        this._amount = amount;
        document.querySelector('#Shop .Controls .Controls-buttons .controls-amount').innerHTML = amount;
    }

    isValid () {
        Messages().clearMessages();

        if (!this._cart.length) {
            Messages().error.write('isValid', 'Le panier est vide.');
            return false;
        }

        if (!Object.keys(this._caster).length) {
            Messages().error.write('isValid', 'Emetteur non défini.');
            return false;
        }

        if (!Object.keys(this._parent).length) {    
            Messages().error.write('isValid', 'Parent non défini.');
            return false;
        }
        
        // Check payment type
        // DIR
        if (this._type > 1) {
            if (!this._ref) {
                Messages().error.write('isValid', 'Veuillez entrer une référence pour le paiement.');
                return false;
            }
        }
        // OFF
        else if (this._type === 1) {
            this._ref = '';
        }
        // Anything else
        else {
            Messages().error.write ('isValid', 'Type de paiement inconnu.');
            return false;
        }

        if (true || App.caster.isAdmin) {

            this.toLocalStorage();
    
            // const child = window.localStorage.getItem('shop_child');
            window.location = '/resume-prestations/' + this.child_id;
        }
        else {
            $('.ui.modal.parent-payment').modal('show');
            
            const link = getVadsLink(
                this._parent.id,
                this._parent.auth.email,
                this._amount,
                this._cart
            );
            
            document.getElementById('vads_link').href = link;
        }
        
    }

    toLocalStorage () {
        window.localStorage.setItem('ShopOrder', JSON.stringify({
            // 'name': this.name,
            'comment': this._comment,

            'amount': this._amount,
            
            'caster': this._caster.id,
            'payer': this._parent.id,
            
            'cart': this._cart,

            'type': this._type,
            'reference': this._ref,
        }));
    }
    
    // Display child tab
    setActiveChildView (child_id=0) {
        if (this._has_errors) {
            Messages().error.write('setActiveChildView', this._error_msg);
            return false;
        }


        if (!child_id) {
            return this.setActiveChildView(
                document
                .querySelector(`#Shop .Children-Records .Children .ui.label`)
                .getAttribute('data-child')
            );
        }

        try {
            const child = document.querySelector(`#Shop .Children-Records .Children .ui.label[data-child="${child_id}"]`);
            
            if (child.classList.contains('active')) {
                return true;
            }
            else {
                // Get active Child/Record/View
                const a_child = document.querySelector('#Shop .Children-Records .Children .ui.label.active');
                const a_record = document.querySelector('#Shop .Children-Records .Records .card.active');
                const a_view = document.querySelector('#Shop .View .ChildView.active');
                
                // Remove active class
                if (a_child) a_child.classList.remove('active');
                if (a_record) a_record.classList.remove('active');
                if (a_view) a_view.classList.remove('active');

                // Get valid Record/View by ID
                const record = document.querySelector(`#Shop .Children-Records .Records .card[data-child="${child_id}"]`);
                const view = document.querySelector(`#Shop .View .ChildView[data-child="${child_id}"]`);
                
                // Active them
                if (child) child.classList.add('active');
                if (record) record.classList.add('active');
                if (view) view.classList.add('active');

                return true;
            }
        }
        catch (e) {
            console.error(e);
            this.setActiveChildView();
            return false;
        }
    }

    // Toggle a PERIOD and his categories
    togglePeriod (period) {
        const REF = {
            'GARDERIE': ['PERISCOLAIRE'],
            'MERCREDIS': ['SEPTEMBRE', 'OCTOBRE', 'NOVEMBRE', 'DECEMBRE', 'JANVIER', 
                          'FEVRIER', 'MARS', 'AVRIL', 'MAI', 'JUIN', 'JUILLET'],
            'VACANCES': ['TOUSSAINT', 'NOEL', 'CARNAVAL', 'PAQUES', 
                         'GRDS_VACANCES_JUILLET', 'GRDS_VACANCES_AOUT'],
        };

        // PERIOD LABEL
        document
        .querySelectorAll(`#Shop .View .ChildView .Filters .ui.label[data-category="${period}"]`)
        .forEach(cat => {
            cat.classList.toggle('active');
        });

        // PRODUCTS
        for (const category of REF[period]) this.toggleCategory(category);
    }

    // Toggle a category
    toggleCategory (category_slug) {
        try {
            document
            .querySelectorAll(`#Shop .View .ChildView .Filters .ui.label[data-category="${category_slug}"]`)
            .forEach(cat => {

                cat.classList.toggle('active');

            });

            document.querySelectorAll(`#Shop .View .ChildView .Products .ProductCategory.${category_slug}`)
            .forEach(product => {
                product.classList.toggle('active');
            });
        }
        catch (e) {
            console.log(`${category_slug} : ${e}`);
            return false;
        }
    }

    // SEE setCategoryFlag
    // Activate a category
    setActiveCategory (category_slug) {
        try {
            document
            .querySelectorAll(`#Shop .View .ChildView .Category .ui.label[data-category="${category_slug}"]`)
            .forEach(cat => {
    
                if (!cat.classList.contains('active')) {
                    cat.classList.add('active');
                }
            });

            document.querySelectorAll(`#Shop .View .ChildView .Products .ProductCategory.${category_slug}`)
            .forEach(product => {
                product.classList.add('active');
            });
        }
        catch (e) {
            console.log(`${category_slug} : ${e}`);
            return false;
        }
    }

    // Activate/De-activate a category
    setCategoryFlag (category_slug, flag) {
        try {
            document
            .querySelectorAll(`#Shop .View .ChildView .Category .ui.label[data-category="${category_slug}"]`)
            .forEach(cat => {
    
                if (cat.classList.contains('active') !== flag) {
                    cat.classList.toggle('active');
                }
            });

            if (flag) {
                document.querySelectorAll(`#Shop .View .ChildView .Products .ProductCategory.${category_slug}`)
                .forEach(product => {
    
                    product.classList.add('active');
                });
            }
            else {
                document.querySelectorAll(`#Shop .View .ChildView .Products .ProductCategory.${category_slug}`)
                .forEach(product => {
    
                    product.classList.remove('active');
                });
            }

        }
        catch (e) {
            console.log(`${category_slug} : ${e}`);
            return false;
        }
    }

    // Open categories for a given month
    setCategoriesByMonth (month) {
        /**
         * month (int) => month from 0 to 11
         */

        const REF = [
            ['JANVIER', 'FEVRIER'],
            ['FEVRIER', 'CARNAVAL', 'MARS'],
            ['MARS', 'AVRIL'],
            ['AVRIL', 'MAI', 'PAQUES'],
            ['MAI', 'JUIN'],
            ['JUIN', 'JUILLET', 'GRDS. VACANCES JUILLET'],
            ['JUILLET', 'GRDS. VACANCES JUILLET', 'AOUT', 'GRDS. VACANCES JUILLET'],
            ['AOUT'],
            ['SEPTEMBRE', 'OCTOBRE', 'TOUSSAINT'],
            ['OCTOBRE', 'TOUSSAINT', 'NOVEMBRE'],
            ['NOVEMBRE', 'DECEMBRE', 'NOEL'],
            ['DECEMBRE', 'NOEL', 'JANVIER']
        ];

        console.log(REF[month]);

        for (const m of REF[month]) {
            this.setActiveCategory(m);
            // for (const m of months) {
            // }
        }
    }

    // Activate/Deactivate all categories by flag
    setCategoriesFlag (flag) {
        const REF = [
            'PERISCOLAIRE',
            'SEPTEMBRE',
            'OCTOBRE',
            'TOUSSAINT',
            'NOVEMBRE',
            'DECEMBRE',
            'NOEL',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'CARNAVAL',
            'AVRIL',
            'PAQUES',
            'MAI',
            'JUIN',
            'JUILLET',
            'GRDS. VACANCES JUILLET',
            'AOUT',
            'GRDS. VACANCES AOUT',
        ];

        REF.forEach(x => this.setCategoryFlag(x, flag));
    }

    setMainProduct (category_slug, child_id, flag) {
        const ctx = this;
        if (this._products.hasOwnProperty(category_slug)) {
            document
            .querySelectorAll(`#Shop .View .ChildView[data-child="${child_id}"] .ProductCategory.${category_slug} .product-tile[data-product]`)
            .forEach(item => {
                if (item.classList.contains('normal') || 
                    item.classList.contains('selected')) {  
                    const product_id = item.getAttribute('data-product');
                    ctx.setProductType(child_id, product_id, item, flag);
                } 
            });
        }
    }

    // Update product tile
    toggleProductType (child_id, product_id) {
        const target = document.querySelector(`#Shop .View .ChildView[data-child="${child_id}"] .product-tile[data-product="${product_id}"]`);

        if (target.classList.contains('normal')) return this.setProductType(child_id, product_id, target, true);
        else if (target.classList.contains('selected')) return this.setProductType(child_id, product_id, target, false);
        else return false;
    }
    
    setProductType (child_id, product_id, target, flag) {
        console.log('1');
        let product = () => { for (const _ of this._raw_products) if (_.id === parseInt(product_id)) return _; }
    
        if (!product()) {
            console.log('product is undefined')
            return 0;
        }
        
        if (this.updateCart(parseInt(product_id), parseInt(child_id), flag)) {
    
            let price = parseInt(target.querySelector('.price .price__amount').innerHTML);
    
            if (product().category === 1) {
                for (const cart of this._cart) {
                    if (cart.product === parseInt(product_id)) {
                        const TARIFS = [20, 32, 40, 60];
                        
                        const len = Math.min(cart.children.length - 1, 3);

                        if (len) {
                            const mod = (flag) ? -1 : 1;
                            const old_tarif = TARIFS[Math.min(len + mod)];
                            const cur_tarif = TARIFS[len];
                            
                            console.log(old_tarif);
                            console.log(cur_tarif);
                            
                            price = Math.abs(cur_tarif - old_tarif);
                            console.log(price);
                        }
                        else {
                            price = (flag) ? 20 : 12;
                        }
                    }
                }
            }
            
            if (flag) {
                target.className = 'product-tile selected';

                this.setAmount(this._amount + price);
                this.setSelectedProducts(this._selectedProducts + 1);
            }
            else if (!flag) {
                target.className = 'product-tile normal';

                // Make sure "select all" is false
                target.parentElement.querySelector('.product-tile.main input[type="checkbox"]').checked = false;
                
                this.setAmount(this._amount - price);
                this.setSelectedProducts(this._selectedProducts - 1);
            }

            return true;
        }

        return false;
    }

    // Update cart state
    updateCart(product, child, flag) {
        /**
         *  @return {true} if update succeed (add/remove)
         *  @return {false} if update failed
         */

        // Cart lookup
        for (var i = 0; i < this._cart.length; ++i) {

            // { product: id, children: [] } 
            const month = this._cart[i];

            // If product exist
            if (month['product'] === product) {

                // Is child in ?
                let index = month['children'].indexOf(child);

                // Should add child
                if (flag) {
                    // If found
                    if (index === -1) {
                        month['children'].push(child);
                        return true;
                    }
                    else {
                        return false;
                    }
                }
                else {
                    // If found
                    if (index === -1) {
                        return false;
                    }
                    else {
                        month['children'].splice(index, 1);
        
                        // if children list is empty remove it
                        if (!month['children'].length)
                            this._cart.splice(i, 1);
        
                        return true;
                    }
                }
            }
        }

        if (flag) {
            // if product was not in cart
            this._cart.push({
                'product': product,
                'children': [child]
            });

            return true;
        }

        return false;
    }




    // EVENTS & TRIGGERS
    //

    onButtonCancelClick (e) {
        window.localStorage.removeItem('ShopOrder');

        if (App.caster.isAdmin) {
            window.close();
        }
        else {
            window.location.reload();
        }
    }

    onButtonPreviousClick (e) { window.close(); }

    onButtonContinueClick (e) {
        if (this.isValid()) {

        }
    }

    onRefChanged (e) {
        // console.log(e.target.value);
        this._ref = e.target.value;
    }

    onTypeChanged (e) {
        this._type = parseInt(e.target.value);
    }

    onCommentChanged (e) {
        this._comment = e.target.value;
    }

    // On child name label click
    onChildLabelClick (e) {
        const el = e.target;

        const target_id = el.getAttribute('data-child');
        if (!target_id) {
            return false;
        }

        console.log(target_id);

        this.setActiveChildView(target_id);
    }

    // On View period label click
    onPeriodClick (e) {
        const el = e.target;

        const period = el.innerHTML.replace(/ /g, '');
        if (!period) {
            return false;
        }

        this.togglePeriod(period);
    }

    // On View category label click
    onCategoryClick (e) {
        const el = e.target;

        const category = el.innerHTML.replace(/ /g, '');
        if (!category) {
            return false;
        }

        this.toggleCategory(category);
    }

    //
    onMainProductTileClick (e) {
        e.preventDefault();

        let target = e.target;
        while (!target.classList.contains('product-tile')) {
            target = target.parentElement;
        }

        const category = target.getAttribute('data-category');

        const chk = target.querySelector('input');

        // Should checkbox be checked
        if (e.target.localName !== 'input') {
            chk.checked = !chk.checked;
        }

        const ctx = this;

        // Search ChildView where event comes from
        document.querySelectorAll('#Shop .View .ChildView').forEach((item) => {
            console.log(item);
            if (item.querySelector(`.product-tile.main[data-category="${category}"]`) === target) {

                // console.log(item.getAttribute('data-child'));
                ctx.setMainProduct(category, item.getAttribute('data-child'), chk.checked);
            }
        });
    }

    //
    onProductTileClick (e) {
        e.preventDefault();

        let target = e.target;
        while (!target.classList.contains('product-tile')) {
            target = target.parentElement;
        }

        const product_id = target.getAttribute('data-product');
        // const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');

        const ctx = this;

        // Search ChildView where event comes from
        document.querySelectorAll('#Shop .View .ChildView').forEach((item) => {
            if (item.querySelector(`.product-tile[data-product="${product_id}"]`) === target) {

                // console.log(item.getAttribute('data-child'));
                ctx.toggleProductType(item.getAttribute('data-child'), product_id);
            }
        });
    }
}

/**
 * LEGACY
 * DO NOT REMOVE BOLOW
 */



class _Shop {
    constructor(params) {
        
    }

    /**
     * SHOP AND SUMMARY
    */

    updateIntels (caster, parent) {
        this.updateIntelsCaster(caster);
        this.updateIntelsParent(parent);
        this.updateIntelsCredit(parent);
    }
    
    updateIntelsCaster (caster) {
        macro_innerHTML('.Intels-caster .Intels__first_name', caster.first_name);
        macro_innerHTML('.Intels-caster .Intels__last_name', caster.last_name);

        return true;
    }

    updateIntelsParent (parent) {
        macro_innerHTML('.Intels-parent .Intels__first_name', parent.first_name);
        macro_innerHTML('.Intels-parent .Intels__last_name', parent.last_name);

        if (parent.emails && parent.emails.length)
            macro_innerHTML('.Intels-parent .Intels__email', parent.email);
        else
            macro_innerHTML('.Intels__email', '<i>Pas d\'email.</i>');

        return true;
    }

    updateIntelsCredit (parent) {
        if (parent.client)
            macro_innerHTML('.Intels-credit .Intels__credit', parent.client.credit['amount']);
        return true;
    }


    /**
     * CART META
     * Items selected
     * Amount
     * Payment modal amount
     */
    updateCartMeta (amount, itemsSelected) {
        document.querySelectorAll('.controls-amount').forEach((item) => { item.innerHTML = amount });
        document.querySelectorAll('.controls-items_selected').forEach((item) => { item.innerHTML = itemsSelected });

        // Payment modal amount
        const x = document.getElementById('payment-amount');
        if (x)
            x.innerHTML = amount;
    }


    /**
     * 
     */
    initModal () {
        const self = this;

        document
            .getElementById('span-close-modal')
            .addEventListener('click', () => {
                self.toggleModal(false);
            });
    }


    toggleModal (flag) {
        if (flag)
            document.getElementById('payment-modal').className = 'my-modal';
        else
            document.getElementById('payment-modal').className = 'my-modal hide';
    }


    modal_setAmount (amount) { document.getElementById('payment-amount').innerHTML = amount;    }
    
    
    /**
     * SHOP 
     */


    pay () {

    }
}


var __Shop = {

    init() {
        this.child = 0;
        this.children = {};

        this.sibling = {};

        this.products = {};
        this.products_snippets = {};

        this.cart = { 'peri': [], 'alsh': [] };
        this.amount = 0;
        this.items_selected = 0;
        
        this.initCaster();

        this.order = new Order;
        this.order.setCaster(App.caster.id);
    },


    initCaster() {
        this.caster = JSON.parse(
            window.localStorage.getItem('caster')
        );

        if (!this.caster) {
            return false;
        }
        return true;
    },


    /**
     * Set variables
     */
    setSibling (raw) {
        this.sibling = JSON.parse(raw);

        this.order.setPayer(this.sibling.parent.id);
    },


    setProducts (raw) {
        this.products = JSON.parse(raw);

        this.products_snippets = this.Products.order(this.products);
    },


    setAmount (amount) {
        this.amount += amount;
        this.UI.updateAmount(this.amount);
    },

    setItemsSelected (itemsSelected) {
        this.items_selected += itemsSelected;
        this.UI.updateItemsSelected(this.items_selected);
    },


    Controls: {},



    UI: {
        render_breadcrumbs() {},


        updateStatus (status) {
            document
            .querySelectorAll('#Controls .Controls-alert')
            .forEach((item) => {
                item.innerHTML = status;
                item.classList.add('show');
            });
        },


        updateAmount (amount) {
            document.querySelector('#Controls .controls-amount').innerHTML = amount;
        },


        updateItemsSelected (itemsSelected) {
            document.querySelector('#Controls .controls-items_selected').innerHTML = itemsSelected;
        },
    },


    Children: {

        init() {
            // Old
            //
            // Get children list
            // And update SearchList
            // 
            // this.getChildrenList(
            //     this.getChildrenList_onSuccess,
            //     this.getChildrenList_onFailure
            // );

            // Old 2 - lol
            //
            // Check there is children
            // if (!Object.keys(children).length) {
            //     // Show error
            //     return false;
            // }

            // Create HTML list
            // Shop.Children.SearchList.updateList(children);


            // New
            //
            // Check localStorage for previous instance
            this.initSelected();

            return true;
        },


        /**
         * OLD FOR API
         * 
         * Fetch children from API
         * @param {*} onSuccess 
         * @param {*} onFailure 
         */
        getChildrenList: function (onSuccess, onFailure) {
            App.API.get('/users/children/')
                .then((data) => {
                    onSuccess(data);
                })
                .catch((err) => {
                    onFailure(err);
                });
        },


        /**
         * On Success
         * - Update list with children
         * - Check local storage
         */
        getChildrenList_onSuccess (data) {
            // Sanity Check
            console.log(data.users.length);

            // Create HTML list
            _Shop.Children.SearchList.updateList(data.users);

            // Check localStorage for previous instance
            const child = window.localStorage.getItem('shop_child');
            if (child)
                _Shop.Children.SearchList.updateSelected(parseInt(child));
        },
        
        
        /**
         * On Failure - Update status 
         */
        getChildrenList_onFailure (err) {
            console.log(err);
        },


        /**
         * Check localStorage for previous instance
         */
        initSelected () {
            const child = window.localStorage.getItem('shop_child');
            if (child)
                this.updateSelected(parseInt(child));
        },


        /**
             * Set active LIST item
             * Create SELECTED item
             */
        updateSelected (id) {
            _Shop.child = id;

            // Set item to active
            const x = document.querySelector(`#SearchList #List-items .list-group-item[data-child="${id}"]`);
            x.classList.add('active');

            // Create element
            let li = document.createElement('li')
                li.className = 'list-group-item';
                li.innerHTML = x.innerHTML;
                li.addEventListener('click', this.selected_onClick);

            // Append element
            document
                .querySelector('#SearchList #List-selected .list-group')
                .appendChild(li);
        },


        /**
         * Reset LIST item
         * Reset SELECTED item
         */
        resetSelected: function () {
            // Reset child id
            _Shop.child = 0;

            // Reset selected HTML
            document.querySelector('#SearchList #List-selected .list-group').innerHTML = '';

            // Reset active item if exist
            const x = document.querySelector('#SearchList #List-items .list-group .list-group-item.active');
            if (x)
                x.classList.remove('active');
        },


        /**
         * Remove items in local storage
         * Triggered by cancel button of controls
         */
        cancel () {
            window.localStorage.removeItem('order');
            window.localStorage.removeItem('order_id');

            window.localStorage.removeItem('shop_child');

            window.location.href = '/intern/home';
        },


        /**
         * Save child ID in local storage
         * Triggered by continue button of controls
         */
        continue() {
            // if (!_Shop.Children.SearchList.hasSelected()) {

            //     _Shop.UI.updateStatus('Veuillez sélectionner un enfant.');

            //     return false;
            // }

            if (!_Shop.child || _Shop.child === '0') {

                _Shop.UI.updateStatus('Veuillez sélectionner un enfant.');

                return false;
            }

            window.localStorage.setItem('shop_child', '' + _Shop.child);
            window.open(
                '/intern/shop/shop/' + _Shop.child,
                '_blank'
            );
        },


        /**
         * Filter children list by value
         * Triggered by the search bar
         * @param {*} value 
         */
        search (value) {
            if (value.length === 0) {
                this.search_reset();
            }
            else if (value.length > 2) {
                this.search_update(value);
                // console.log(value);
            }
        },


        /**
         * Reset children list
         * Remove 'hide' class on children list items
         */
        search_reset () {
            document.querySelectorAll('#SearchList #List-items .list-group .list-group-item.hide').forEach((item) => {
                item.classList.remove('hide');
            });
        },


        /**
         * Update/Sort children list by search value
         * @param {*} value 
         */
        search_update (value) {
            document.querySelectorAll('#SearchList #List-items .list-group .list-group-item').forEach((item) => {
                var _item = item.innerHTML.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                var _filter = value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

                // console.log(_item);
                if (!_item.includes(_filter))
                    item.classList.add('hide');
                else
                    item.classList.remove('hide');
            });
        },


        list_onClick: function (e) {
            const id = e.getAttribute('data-child');

            if (e.classList.contains('active'))
                this.resetSelected();

            else {
                this.resetSelected();
                this.updateSelected(id);
            }
        },


        list_onDblClick: function (e) {
            this.list_onClick (e);

            this.continue();
        },


        selected_onClick: function (e) {
            _Shop.Children.resetSelected();
        },



        // Old
        SearchList: {
            
            init () {
                this.filter = '';
            },


            /**
             * True if an item is selected
             * False if not
             */
            hasSelected: function () {
                return Boolean(Shop.child);
            },
    
    
            // Return selected item
            itemSelected: function () {
                return Shop.child;
            },
    
    
            /**
             * Parse children
             * And render list
             */
            updateList: function (children) {
                const x = document.querySelector('#SearchList #List-items .list-group');
    
                children.forEach((child) => {
                    const z = `#${child.id} - ${child.first_name} ${child.last_name} ${(child.dob) ? ' - ' + child.dob : ''}`;
                    
                    Shop.children[child.id] = z;
                    
                    let li = document.createElement('li')
                        li.className = 'list-group-item';
                        li.setAttribute('data-child', child.id);
                    
                    li.addEventListener('click', this.list_onClick);
                    li.addEventListener('dblclick', this.list_onDblClick);
                    
                    li.innerHTML = z;
    
                    x.appendChild(li);
                });
            },
    
    
            /**
             * Apply a filter on LIST item
             * 
             */
            updateFilter: function (value) {
                this.filter = value;
                
                document.querySelectorAll('#SearchList #List-items .list-group .list-group-item').forEach((item) => {
                    var _item = item.innerHTML.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
                    var _filter = value.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    
                    // console.log(_item);
                    if (!_item.includes(_filter))
                        item.classList.add('hide');
                    else
                        item.classList.remove('hide');
                });
            },
    
            
            /**
             * Set active LIST item
             * Create SELECTED item         * 
             */
            updateSelected: function (id) {
                Shop.child = id;
    
                // Set item to active
                document
                    .querySelector(`#SearchList .list-group-item[data-child="${id}"]`)
                    .classList.add('active');
    
                // Create element
                let li = document.createElement('li')
                    li.className = 'list-group-item';
                    li.innerHTML = Shop.children[id];
                    li.addEventListener('click', this.selected_onClick);
    
                // Append element
                document
                    .querySelector('#SearchList #List-selected .list-group')
                    .appendChild(li);
            },
    
    
            /**
             * Reset LIST item
             * Reset SELECTED item
             */
            resetSelected: function () {
                // Reset child id
                Shop.child = 0;
    
                // Reset selected HTML
                document.querySelector('#SearchList #List-selected .list-group').innerHTML = '';
    
                // Reset active item if exist
                const x = document.querySelector('#SearchList #List-items .list-group .list-group-item.active');
                if (x)
                    x.classList.remove('active');
            },
    
    
            /**
             * Un-hide LIST items
             */
            resetFilter: function () {
                this.filter = '';
    
                document.querySelectorAll('#SearchList #List-items .list-group .list-group-item.hide').forEach((item) => {
                    item.classList.remove('hide');
                });
            },
    
            
            /**
             * 
             */
            search_onInput: function (value) {
                if (value.length === 0) {
                    Shop.Children.SearchList.resetFilter();
                }
                else if (value.length > 2) {
                    Shop.Children.SearchList.updateFilter(value);
                    // console.log(value);
                }
            },
    
    
            /**
             * List item logic
             */
            list_onClick: function (e) {
                const id = e.target.getAttribute('data-child');
    
                if (e.target.classList.contains('active'))
                    Shop.Children.SearchList.resetSelected();
    
                else {
                    Shop.Children.SearchList.resetSelected();
                    Shop.Children.SearchList.updateSelected(id);
                }
            },
    
    
            list_onDblClick: function (e) { },
    
    
            selected_onClick: function (e) {
                Shop.Children.SearchList.resetSelected();
            },
        },


    },


    Shop: {

        init (rsibling, rproducts) {
            Shop.setSibling(rsibling);
            Shop.setProducts(rproducts);
            
            // Sanity check 
            console.log(Shop.sibling);
            console.log(Shop.products);

            // Render UI
            // Render shop head
            this.updateCaster(Shop.caster);
            this.updateParent(Shop.sibling.parent);

            // Render shop body - Tabs
            this.updateHeaders(Shop.sibling.children);
            this.updateBody(Shop.sibling.children);

            // Render children orders
            this.updateOrders();

            this.updateEvents();
        },


        cancel () {
            window.localStorage.removeItem('order');
            window.localStorage.removeItem('order_id');

            window.localStorage.removeItem('shop_child');

            window.close();
        },


        return () {
            window.close();
        },


        continue () {
            const payload = Shop.order.payload();
            console.log(payload);

            if (!payload) {
                Shop.UI.updateStatus('Veuillez sélectionner un produit.');

                return false;
            }

            Shop.order.create();

            // window.localStorage.setItem('shop_order', JSON.stringify(payload));
            // window.open(
            //     '/intern/shop/shop/' + Shop.child,
            //     '_blank'
            // );
            return true;
        },


        updateCaster (caster) {
            const x = document.querySelector('#Intels #Intels-caster');

            x.querySelector('.Tab-intels__first_name').innerHTML = caster.first_name;
            x.querySelector('.Tab-intels__last_name').innerHTML = caster.last_name;

            return true;
        },


        updateParent (parent) {
            const x = document.querySelector('#Intels #Intels-parent');

            x.querySelector('.Tab-intels__first_name').innerHTML = parent.first_name;
            x.querySelector('.Tab-intels__last_name').innerHTML = parent.last_name;

            if (parent.emails.length)
                x.querySelector('.Tab-intels__email').innerHTML = parent.email;
            else 
                x.querySelector('.Tab-intels__email').innerHTML = '<i>Pas d\'email.</i>';

            return true;
        },


        updateHeaders (children) {
            // if (!children.length) {
            //     return false;
            // }

            // Macro: Create item
            const createItem = (index, child, active = false) => {
                const li = document.createElement('li');

                li.setAttribute('data-id', child['id']);
                // li.setAttribute('data-index', index);

                li.classList.add('Tabs-header-item');
                if (active)
                    li.classList.add('active');
                    
                li.onclick = Shop.Shop.renderHeader_onClick
                li.innerHTML = child['first_name'];

                return li;
            };
            
            // 
            const group = document.querySelector('#Tabs-header .Tabs-header-group');

            // Create items
            Object.values(children).forEach((child, index) => {
                // Create 1st item as active
                if (!index)
                    group.appendChild(createItem(index, child, true));

                else
                    group.appendChild(createItem(index, child));
            });

            return true;
        },


        updateBody: function (children) {
            const group = document.querySelector('#Tabs-body .Tabs-body-group');
            
            const snippets = Shop.products_snippets;
            
            Object.values(children).forEach((child, index) => {
                let snippet = '';
                
                // Render 1st child as active
                if (child['record']['classroom'] >= 1 &&
                    child['record']['classroom'] <= 4) {
                    snippet = snippets['snippet_m6'];
                }
                else {
                    snippet = snippets['snippet_p6'];
                }

                if (!index)
                    group.appendChild(this.updateBody_item(index, child, snippet, true));

                else
                    group.appendChild(this.updateBody_item(index, child, snippet));
            });
        },


        updateBody_item: function (index, child, products, active = false) {
            let products_ul = document.createElement('ul');
                products_ul.innerHTML = products;
                products_ul.className = 'Tabs-body-child-products';
                // products_ul.setAttribute('data-id', child['id']);
                // products_ul.setAttribute('data-index', index);

            let record_ul = document.createElement('ul');
                record_ul.className = 'Tabs-body-child-record';
                record_ul.innerHTML = this.updateBody_record(child['record']);

            let wrapper_content = document.createElement('div');
                wrapper_content.className = 'wrapper-content';

                wrapper_content.appendChild(record_ul);
                wrapper_content.appendChild(products_ul);

            let title = document.createElement('p');
                title.className = 'title';
                title.innerHTML = child['first_name'];

            let wrapper_title = document.createElement('div');
                wrapper_title.className = 'wrapper-title';

                wrapper_title.appendChild(title);

            let wrapper = document.createElement('div');
                wrapper.className = 'wrapper';

                wrapper.appendChild(wrapper_title);
                wrapper.appendChild(wrapper_content);

            let li = document.createElement('li');
                li.className = 'Tabs-body-child ' + ((active) ? 'active' : '');
                li.setAttribute('data-id', child['id']);



                li.appendChild(wrapper);

            return li;
        },


        updateBody_record: function (record) {
            const classroom = Shop.Utils.RECORD_CLASSROOM[record['classroom']];
            const quotient_q1 = Shop.Utils.RECORD_QUOTIENT[record['caf']['quotient_q1']];
            const quotient_q2 = Shop.Utils.RECORD_QUOTIENT[record['caf']['quotient_q2']];

            return `<li><b>Ecole: </b>          <span class="record-school">        ${record['school']}</span></li>
                    <li><b>Classe: </b>         <span class="record-classroom">     ${classroom}</span></li>
                    <li><b>Quotient 2019: </b>  <span class="record-quotient-q1">   ${quotient_q1}</span></li>
                    <li><b>Quotient 2020: </b>  <span class="record-quotient-q2">   ${quotient_q2}</span></li>`;
        },

        
        updateOrders: function () {
            const children = Shop.sibling['children'];
            const values = Object.values(children);

            for (let i = 0; i < values.length; ++i) {
                const child = values[i];

                if (!child['tickets'])
                    continue;

                for (let j = 0; j < child['tickets'].length; ++j) {
                    const ticket = child['tickets'][j];

                    // Handle ticket status
                    if (!ticket['status'][0]) {
                        console.log(`No status for ticket (${ticket['id']}) with payee (${ticket['payee']})`);
                        continue;
                    }
                    
                    let status = '';
                    switch (ticket['status'][0]['status']) {
                        // Reserved
                        case 1:
                            break;

                        // Completed
                        case 2:
                            status = 'purchased';
                            break;
                    
                        default:
                            break;
                    }

                    // Sanity check
                    // console.log(status);

                    const e = document.querySelector(`.Tabs-body-child[data-id="${ticket['payee']}"] .product-tile[data-id="${ticket['product']}"]`);
                    
                    if (!e) {
                        console.log('Failed to found product for children');
                        continue;
                    }

                    // Add class status
                    e.classList.add(status);
                    e.classList.remove('normal');

                    const _date = e.querySelector('.product-meta-bought span');
                    if (_date)
                        _date.innerHTML = this.ticketDateToHTML(ticket['status'][0]['date']);
                };
            };
        },


        updateEvents: function () {
            // Tab header events
            document
            .querySelectorAll('#Tabs-header .Tabs-header-item')
            .forEach(item => item.addEventListener('click', (e) => {

                // Unset active items 
                document.querySelector('.Tabs-header-item.active').classList.remove('active');
                document.querySelector('.Tabs-body-child.active').classList.remove('active');
                
                // Find target ID
                const id = e.target.getAttribute('data-id');

                // Set new active items
                e.target.classList.add('active');
                document.querySelector(`.Tabs-body-child[data-id="${id}"]`).classList.add('active');
            }));


            // Product tile event
            document
            .querySelectorAll('#Tabs-body .product-tile')
            .forEach((item) => {
                item.addEventListener('click', function (e) {
                    e.preventDefault();

                    let target = e.target;
                    while (!target.classList.contains('product-tile')) {
                        target = target.parentElement;
                    }

                    // console.log(target);

                    const product_id = target.getAttribute('data-id');
                    // const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');

                    document.querySelectorAll('.Tabs-body-child').forEach((item) => { 
                        if (item.querySelector(`.product-tile[data-id="${product_id}"]`) === target) { 
                            
                            // console.log(item.getAttribute('data-id'));
                            Shop.Shop.toggleProduct(item.getAttribute('data-id'), product_id);
                        } 
                    });

                    // Shop.Shop.toggleProduct(child_id, product_id);
                });
            });
        },


        toggleProduct: function (child_id, product_id) {

            var target = document.querySelector(`.Tabs-body-child[data-id="${child_id}"] .product-tile[data-id="${product_id}"]`);

            if (target.classList.contains('normal') ||
                target.classList.contains('selected')) {

                if (Shop.Shop.toggleProduct_item(parseInt(child_id), parseInt(product_id))) {
                    target.className = 'product-tile selected';
                }
                else {
                    target.className = 'product-tile normal';
                }
            }

            return;
        },


        toggleProduct_item: function (child_id, product_id) {
            // Product lookup
            let product = undefined;
            for (var i = 0; i < Shop.products.length; ++i) {
                if (Shop.products[i]['id'] === product_id) {
                    product = Shop.products[i];
                    break;
                }
            }

            if (!product) {
                console.log('products === undefined')
                return 0;
            }

            let is_selected = false;

            // PERI
            if (product['category'] === 1) 
                is_selected = Shop.order.togglePeri(product_id, child_id)
            else
                is_selected = Shop.order.toggleAlsh(product_id, child_id)
            
            
            // Update Cart Meta
            if (is_selected) {
                Shop.setAmount(product['price']);
                Shop.setItemsSelected(1);
            }
            else {
                Shop.setAmount(-product['price']);
                Shop.setItemsSelected(-1);
            }

            // updateCartMeta();
            // cart_save();

            return is_selected;
        },


        ticketDateToHTML: function (date) {
            let x = date.split('T')[0];
                x = x.split('-');
            return `${x[2]}-${x[1]}-${x[0]}`;
        },


        // Old function
        _toggleProduct_item: function (child_id, product_id) {
            // Product lookup
            let product = undefined;
            for (var i = 0; i < Shop.products.length; ++i) {
                if (Shop.products[i]['id'] === product_id) {
                    product = Shop.products[i];
                    break;
                }
            }

            if (!product) {
                console.log('products === undefined')
                return 0;
            }

            var is_selected = false;

            // PERI
            if (product['category'] === 1) {
                var found = false;
                for (var i = 0; i < Shop.cart['peri'].length; ++i) {
                    const month = Shop.cart['peri'][i];

                    if (month['product'] === product_id) {

                        let index = -1;
                        if ((index = month['children'].indexOf(child_id)) === -1) {
                            month['children'].push(child_id);

                            Shop.amount += product['price'];
                            ++Shop.items_selected;

                            is_selected = true;
                        }
                        else {
                            month['children'].splice(index, 1);

                            Shop.amount -= product['price'];
                            --Shop.items_selected;

                            // If children is empty remove month
                            if (!month['children'].length)
                                Shop.cart['peri'].splice(i, 1);
                        }
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    Shop.cart['peri'].push({
                        'product': product_id,
                        'children': [child_id]
                    });
                    Shop.amount += product['price'];
                    ++Shop.items_selected;

                    is_selected = true;
                }
            }
            // ALSH
            else {
                for (var i = 0; i < Shop.cart['alsh'].length; ++i) {
                    var found = false;
                    if (Shop.cart['alsh'][i]['child'] === child_id) {

                        let index = -1;
                        if ((index = Shop.cart['alsh'][i]['products'].indexOf(product_id)) === -1) {
                            Shop.cart['alsh'][i]['products'].push(product_id);

                            Shop.amount += product['price'];
                            ++Shop.items_selected;

                            is_selected = true;
                        }
                        else {
                            Shop.cart['alsh'][i]['products'].splice(index, 1);

                            Shop.amount -= product['price'];
                            --Shop.items_selected;

                            if (!Shop.cart['alsh'][i]['products'].length)
                                Shop.cart['alsh'].splice(i, 1);
                        }
                        found = true;
                        break;
                    }
                }
                if (!found) {
                    Shop.cart['alsh'].push({
                        'child': child_id,
                        'products': [product_id]
                    });
                    Shop.amount += product['price'];
                    ++Shop.items_selected;

                    is_selected = true;
                }
            }

            console.log(Shop.cart['peri']);
            console.log(Shop.cart['alsh']);


            // Update Cart Meta
            const controls = document.querySelector('#Shop .Controls');

            // Controls.updateItemsSelected(controls, items_selected);
            // Controls.updateAmount(controls, amount);


            // updateCartMeta();
            // cart_save();

            return is_selected;
        },


    },


    Utils: {
        RECORD_QUOTIENT: [
            '<i>AUCUN</i>',
            'NE',
            'Q2',
            'Q1',
        ],

        RECORD_CLASSROOM: [
            '<i>AUCUN</i>',
            'STP',
            'SP',
            'SM',
            'SG',
            'CP',
            'CE1',
            'CE2',
            'CM1',
            'CM2',
        ],
    },


    Products: {
        CATEGORY: [
            '',
            'PERI',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'AVRIL',
            'MAI',
            'JUIN',
            'JUILLET',
            'AOUT',
            'SEPTEMBRE',
            'OCTOBRE',
            'NOVEMBRE',
            'DECEMBRE',
            'TOUSSAINT',
            'NOEL',
            'CARNAVAL',
            'PAQUES',
            'GRDS_VACANCES_JUILLET',
            'GRDS_VACANCES_AOUT',
        ],


        createProduct: function (type, product) {
            return `<li class="product-tile ${type}" data-id="${product.id}">
            <div class="product-tile-head">
                <div class="product-meta-title">${product.name}</div>
            </div>
        
            <div class="product-tile-body">
                <div class="product-meta-add"><i class="fas fa-plus"></i></div>
                <div class="product-meta-ban"><i class="fas fa-ban"></i></div>
                <div class="product-meta-check"><i class="fas fa-check"></i></div>
                <div class="product-meta-selected"><i class="fas fa-cart-arrow-down"></i></div>
                <div class="product-meta-checkbox"><input type="checkbox" onclick=""/></div>
            </div>
        
            <div class="product-tile-footer">
                <div class="product-meta-price">${product.price} E</div>
                <div class="product-meta-bought">payé le <span></span></div>
            </div>
        </li>`;
        },


        order: function (products, alsh = true) {
            let _peri = [];
            let _alsh_m6 = {};
            let _alsh_p6 = {};

            for (var i = 0; i < products.length; ++i) {
                if (products[i]['category'] === 1) {
                    _peri.push(products[i]);
                }
                else {
                    const c = this.CATEGORY[products[i]['category']];

                    if (products[i]['subcategory'] === 1) {
                        if (!_alsh_m6[c])
                            _alsh_m6[c] = [];
                        _alsh_m6[c].push(products[i]);
                    }
                    else if (products[i]['subcategory'] === 2) {
                        if (!_alsh_p6[c])
                            _alsh_p6[c] = [];
                        _alsh_p6[c].push(products[i]);
                    }
                }
            }

            const peri = this.order_peri(_peri);

            if (alsh) {
                const m6 = this.order_alsh(_alsh_m6);
                const p6 = this.order_alsh(_alsh_p6);

                return {
                    'snippet_m6': peri + m6,
                    'snippet_p6': peri + p6,
                };
            }
            else {
                return {
                    'snippet_m6': peri,
                    'snippet_p6': peri,
                };
            }

        },


        order_peri: function (peri) {
            let snippet = '';
            for (var i = 0; i < peri.length; ++i) {
                snippet += this.createProduct('normal', peri[i]);
            }
            return `<li class="product-category">
                <h3 class="product-category-title">PERI</h3>
                <ul class="product-category-products">${snippet}</ul>
            </li>`;
        },


        order_alsh: function (alsh) {
            let snippet = '';
            Object.keys(alsh).forEach((item) => {
                snippet += this.order_alsh_period(item, alsh[item]);
            });
            return snippet;
        },


        order_alsh_period: function (period, products) {
            let snippet = '';
            for (var i = 0; i < products.length; ++i) {
                snippet += `<li class="product-category-product">${this.createProduct('normal', products[i])}</li>`;
            }
            return `<li class="product-category">
                        <h3 class="product-category-title">${period}</h3>
                        <ul class="product-category-products">${snippet}</ul>
                    </li>`;
        },


        ui_products_init: function (onClick) {
            document
                .querySelectorAll('#tabs-body .product-tile')
                .forEach((item) => {
                    item.addEventListener('click', function (e) {
                        e.preventDefault();

                        let target = e.target;
                        while (!target.classList.contains('product-tile')) {
                            target = target.parentElement;
                        }

                        const product_id = target.getAttribute('data-id');
                        const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');

                        onClick(child_id, product_id);
                    });
                });
        },


        ui_products_item_onClick: function (e) {
            e.preventDefault();

            let target = e.target;
            while (!target.classList.contains('product-tile')) {
                target = target.parentElement;
            }

            if (target.classList.contains('main') ||
                target.classList.contains('summary') ||
                target.classList.contains('expired') ||
                target.classList.contains('breaking') ||
                target.classList.contains('purchased')) {
                return;
            }

            const child_id = target.parentElement.getAttribute('data-id');
            const product_id = target.getAttribute('data-id');

            console.log(child_id);
            console.log(product_id);

            switch (cart_toggleItem(product_id, child_id)) {
                case 0:
                    break;

                case 1:
                    target.className = 'product-tile normal';
                    break;

                case 2:
                    target.className = 'product-tile selected';
                    break;
            }
        },
    },

};



// Some old codes I keep in case
var ___Shop = {

    init () {
        this.init_routes();
    },
    
    init_routes () {
        this.router = new Router();

        this.router.add('/intern/shop', req => { this.state_shop(req); });
        this.router.add('/intern/shop/shop', req => { this.state_shop_shop(req); });
        this.router.add('/intern/shop/summary', req => { this.state_shop_summary(req); });
        this.router.add('/intern/shop/children', req => { this.state_shop_children(req); });
    
        this.router.init();
    },


    state_shop (req) {
        console.log(req);
        window.location.href = '/intern/shop/children';
        // this.router.load('/intern/shop/children', 'Shop - Children');
    },
    
    state_shop_shop (req) {
        console.log(req);

    },
    
    state_shop_children (req) {
        console.log(req);
        
        this.Children.init();

    },
    
    state_shop_summary (req) {
        console.log(req);
    },


    UI: {
        render_breadcrumbs () {

        },

        wrapper (title, content) {
            return `<div class="wrapper">
                        <div class="wrapper-title">
                            <p class="title">${title}</p>
                        </div>
                        <div class="wrapper-content">${content}</div>
                    </div>`;
        },
    },


    Children: {

        init () {

            this.render();
        },

        render () {
            const x = document.getElementById('Shop');

            x.innerHTML = Shop.UI.wrapper('Enfants', 'Enfants');
        },
    },


    Shop: {
        init(raw) {
            Shop.sibling = JSON.parse(raw);

            // this.initChild();

            // this.initFamily();
        },


        initChild() {
            Shop.child = JSON.parse(window.localStorage.getItem('shop_child'));
            if (!Shop.child) {
                console.log('!_child');
                return false;
            }
            return true;
        },



        initParent(id) { },


        async initFamily() {
            if (!Shop.child)
                return false;

            // Get siblings
            const family = 0;


            if (!family) {

                return false
            }

            Shop.family = family;
            return true;

            let _siblings = await this.getSiblings(Shop.child);
            if (!_siblings) {
                console.log('!');
                return false;
            }

            // Get parent
            let _parent = await this.getUser(_siblings.parent);
            if (!_parent)
                return false;

            // order['payer'] = _parent.id;

            const parent = _parent;

            // Get children
            console.log('Children:');

            let _children = [];
            for (var i = 0; i < _siblings.siblings.length; ++i) {
                const sibling = _siblings.siblings[i];

                const _child = await this.getUser(sibling.child);
                const _record = await this.getRecord(sibling.child);
                // const _tickets = getTicketsByChild(sibling.child);

                _child['record'] = _record;
                // _child['tickets'] = _tickets;

                // _children.push(_child);

                // console.log(_child);
            }

            // if (!_children.length)
            //     return false;

            // children = _children;

            // window.localStorage.setItem('parent', JSON.stringify(parent));
            // window.localStorage.setItem('children', JSON.stringify(children));

            return true;
        },


        updateCaster() {

        },


        updateParent() { },


        updateTabs() {

        },


        async getSiblings(id) {
            return await App.API.get(`/v1/siblings/child/${id}`)
                .then(function (data) {
                    const siblings = data.siblings;
                    console.log(siblings);
                    return siblings;
                }, function (err) {
                    console.log('Failed to get siblings for parent: ' + id);
                    return false;
                });
        },


        async getUser(id) {
            return await App.API.get(`/users/${id}`)
                .then(function (data) {
                    const user = data.user;
                    console.log(user);
                    return user;
                }, function (err) {
                    console.log('Failed to get user for id: ' + id);
                    return false;
                });
        },


        async getRecord(id) {
            return await App.API.get(`/v1/records/child/${id}`)
                .then(function (data) {
                    const record = data.record;
                    console.log(record);
                    return record;
                }, function (err) {
                    console.log('Failed to get record');
                    return false;
                });
        },
    },
};


// const CLASSROOMS = [
//     '<i>pas de classe</i>',
//     'STP',
//     'SP',
//     'SM',
//     'SG',
//     'CP',
//     'CE1',
//     'CE2',
//     'CM1',
//     'CM2',
//     '6ème',
// ];

// const QUOTIENT = [
//     'NE',
//     'NE',
//     'Q2',
//     'Q1',
// ];