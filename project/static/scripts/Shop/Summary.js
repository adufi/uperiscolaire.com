function macro_innerHTML (e, innerHTML) {
    document.querySelectorAll(e).forEach((item) => { item.innerHTML = innerHTML; });
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

        obs = '',
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
            <div class="stock">Stock: ${stock_current} / ${stock_max}</div>
        </div>
    
        <div class="body">
            <div class="icon add"><i class="fas fa-plus"></i></div>
            <div class="icon ban"><i class="fas fa-ban"></i></div>
            <div class="icon check"><i class="fas fa-check"></i></div>
            <div class="icon expired"><i class="icon calendar times outline"></i></div>
            <div class="icon empty"><i class="icon exclamation circle"></i></div>
            <div class="icon selected"><i class="fas fa-cart-arrow-down"></i></div>
            <div class="icon checkbox"><input type="checkbox" onclick=""/></div>
        </div>
    
        <div class="footer">
            <div class="obs">${obs}</div>
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


class Summary {

    constructor () {
        this._caster = undefined;
        this._parent = undefined;
        this._active_school_year = undefined;

        this._children = [];

        this._has_errors = false;
        this._error_msg = '';

        this._cart = [];
        this._order = {
            name: '',
            comment: '',

            type: 2,
            reference: '',

            date: '',

            caster: 0,
            payer: 0,

            amount: 0,
            amount_rcvd: 0,
            amount_refunded: 0,

            tickets: [],
            tickets_invalid: [],
        }

        this._isReady = false;
    }

    setCaster (caster) { this._caster = caster; }
    setActiveSchoolYear (sy) { this._active_school_year = sy; }

    fromAPIv2 (data) {
        if (data.hasOwnProperty('parent')) this.setParent(data.parent);
        if (data.hasOwnProperty('children')) this.setChildren(data.children);
        // if (data.hasOwnProperty('orders')) this.setOrders(data.orders);

        if (data.hasOwnProperty('order')) {
            if (Object.keys(data.order).length) {
                Messages().warning.write('order', 'Une commande est déjà en cours et en attente de paiement. Elle sera donc affichée.<br>Si vous souhaitez annuler la commande veuillez patienter 30 minutes ou contacter nos services.');

                this.fromOrder(data.order);
            }
        }
    }

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

    setParent (parent) {
        this._parent = parent;

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

    setChildren (children) {
        if (children && children.length) {
            for (const child of children) {
                this._children.push(child);
            }
        }
        else {
            this._has_errors = true;
            this._error_msg = 'Aucun enfant trouvé.';
        }   
    }

    isReady () { return this._isReady; }

    fromLocalOrder (order) {
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
            if (!order.type) {
                Messages().warning.write('type', 'Aucun type de reçu pour la référence.');
                return false;
            }
            
            this._cart = order.cart;
            
            this._order.comment = order.comment;

            this._order.type = order.type;
            this._order.reference = order.reference;

            this._order.caster = order.caster;
            this._order.payer = order.payer;

            // this._order.amount = order.amount;

            this.api_verify();

            this._isReady = true;
            return true;
        }
        catch (e) {
            console.error(e);
            return false;
        }
    }

    fromOrder (order) {
        try {
            // Check order integrity (caster/parent)
            // if (order.caster !== this._caster.id) {
            //     Messages().warning.write('toLocalStorage', 'Sauvegarde incorrect (emetteur). Création d\'un nouveau panier.');
            //     return false;
            // }
            
            if (order.payer !== this._parent.id) {
                Messages().warning.write('toLocalStorage', 'Sauvegarde incorrect (parent). Création d\'un nouveau panier.');
                return false;
            }
    
            // Type verification
            if (!order.type) {
                Messages().warning.write('type', 'Aucun type de reçu pour la référence.');
                return false;
            }

            this._order.id = order.id;
            
            this._order.tickets = order.tickets;
            this._order.tickets_invalid = [];
            
            this._order.comment = order.comment;

            this._order.type = order.type;
            this._order.reference = order.reference;

            this._order.caster = order.caster;
            this._order.payer = order.payer;

            this._order.amount = order.amount;
            this._order.amount_rcvd = order.amount_rcvd;

            // this.renderVerify();

            this._isReady = true;
            return true;
        }
        catch (e) {
            console.error(e);
            return false;
        }
    }

    api_verify (onSuccess, onFailure) {
        let self = this;
        if (!this._order.payer && 
            !this._order.caster) {
            Messages().warning.write('api_verify', 'Parent/Emetteur incorrect.');
            return false;
        }

        if (!this._cart.length) {
            Messages().warning.write('api_verify', 'Aucun produit sélectionné.');
            return false;
        }

        App.post(
            '/api/order/verify/',
            JSON.stringify({
                'cart': this._cart,

                'payer': this._order.payer,
                'caster': this._order.caster,
            }), 
            true
        )
        .then((data) => {
            console.log(data);

            self._order.amount = data.amount;
            self._order.tickets = data.tickets;
            self._order.tickets_invalid = data.tickets_invalid;

            self.renderVerify();

            if (onSuccess)
                onSuccess(data);
        })
        .catch((err) => {
            console.log(err);

            // this.verify_response = err;
        
            if (onFailure)
                onFailure(err);
        });

        return true;
    }

    ready () {
        $('.ui.accordion').accordion();
    }

    render () {
        this.render_Controls();
        this.render_Intels();
    }
    
    renderVerify () {
        document.querySelector('#Shop .Controls .Controls-buttons .controls-amount').innerHTML = this._order.amount - this._order.amount_rcvd;

        this.render_Dir();
        this.render_Tickets();

        this.ready();
    }

    // Render Controls
    render_Controls () {
        document.querySelector('#Shop .Controls .Controls-texts').classList.add('d-none');
        
        // document.querySelector('#Shop .Controls .Controls-buttons .controls-amount').innerHTML = this._amount;
        // document.querySelector('#Shop .Controls .Controls-texts .controls-items_selected').innerHTML = this._selectedProducts;
        
        document.querySelector('#Shop .Controls .controls-cancel').onclick = (e) => this.onButtonCancelClick(e);
        document.querySelector('#Shop .Controls .controls-previous').onclick = (e) => this.onButtonPreviousClick(e);
        document.querySelector('#Shop .Controls .controls-pay').onclick = (e) => this.onButtonPayClick(e);
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
        if (this._order.type != 1) {
            document.querySelector('#Shop .Dir-Intels .Dir').classList.remove('hide');
            
            const TYPES = [
                '',
                '',
                'MANUEL',
                'DIRECTRICE',
                'MIGRATION',
                'MIGRATION',
                'PAY ASSO',
                'PAYPAL',
                'STRIPE',
            ];

            const type = (TYPES[this._order.type]) ? TYPES[this._order.type] : '<i>Type inconnu</i>';

            document.querySelector('#Shop .Dir-Intels .Dir-type-label span').innerHTML = type;

            document.querySelector('#Shop .Dir-Intels .Dir-reference-label span').innerHTML = this._order.reference;
        }
        else {
            document.querySelector('#Shop .Dir-Intels .Dir').classList.add('hide');
        }

    }

    render_Tickets () {
        const childrenTickets = this._render_Tickets_sort();

        // this._render_Tickets_UI();

        const intel = this._parent.intel;

        // Create UI
        const body = document.querySelector('.Tabs._Summary .Tabs-body .Tabs-body-group');
        for (const id of Object.keys(childrenTickets)) {

            let child = undefined;
            for (const _ of this._children) {
                if (_.id === parseInt(id)) child = _;
            }

            if (!child) {
                console.log('No child found for ID ' + id);
                continue;
            }
            
            const tickets = childrenTickets[id]['valid'];
            const tickets_invalid = childrenTickets[id]['invalid'];

            // Create wrapper
            let title = child['first_name'];

            let record = child.record;

            if (record) {
                const school = (record['school']) ? record['school'] : '<i>pas d\'école renseignée</i>'
                const classroom = CLASSROOMS[record['classroom']];
                const quotient_2 = QUOTIENT[intel['quotient_2']];
                const quotient_1 = QUOTIENT[intel['quotient_1']];

                title += ' - ' + school;
                title += ` - ${quotient_1}/${quotient_2}`;
            }

            const wrapper = document.createElement('div');
                wrapper.className = 'wrapper';
                // wrapper.setAttribute('data-index', i);
                wrapper.setAttribute('data-child', id);
                wrapper.innerHTML = `<div class="wrapper-title">
                        <p class="title">${title}</p>
                    </div>
                    <div class="wrapper-content">
                        <ul class="product-category-products"></ul>
                    </div>`;

            const content = wrapper.querySelector('.product-category-products');

            const getProduct = (id) => {
                for (const product of this._raw_products) {
                    if (parseInt(id) === product.id) return product;
                }
            };

            console.log(tickets);
            console.log(tickets_invalid);

            // Add tickets
            tickets.forEach((ticket) => {
                const product = getProduct(ticket.product);

                if (product) {
                    console.log('append');
                    content.appendChild(
                        _Product.create({
                            type: 'summary-ok',

                            name: product.name,
                            attributes: {},

                            price: ticket.price,
                        })
                    );
                }
            });

            // Add invalid tickets
            tickets_invalid.forEach((ticket) => {
                let product = undefined;
                if (ticket.product === -1) {
                    product = {
                        'id': -1,
                        'name': 'Erreur'
                    };

                    // Remove child/product from cart
                    for (const item of orderHelper.cart) {
                        // orderHelper.removeProduct(ticket.payee, item.product);
                    }
                    
                }
                else {
                    product = getProduct(ticket.product);
                    // orderHelper.removeProduct(ticket.payee, ticket.product);
                }
                
                if (product) {
                    console.log('append2');
                    content.appendChild(
                        _Product.create({
                            type: 'summary-ban',

                            name: product.name,
                            attributes: {},

                            obs: ticket.obs,
                            price: ticket.price,
                        })
                    );
                }
            });

            body.appendChild(wrapper);
        };
    }

    _render_Tickets_sort () {
        const tickets = this._order.tickets;
        const tickets_invalid = this._order.tickets_invalid;

        const childrenTickets = {};

        // Sort tickets by child
        for (let i = 0; i < tickets.length; ++i) {
            const ticket = tickets[i];

            if (!childrenTickets[ticket.payee])
                childrenTickets[ticket.payee] = {
                    'valid': [],
                    'invalid': []
                };

            childrenTickets[ticket.payee]['valid'].push(ticket);
        }

        for (let i = 0; i < tickets_invalid.length; ++i) {
            const ticket = tickets_invalid[i];

            if (ticket.payee === -1) {
                for (const _ in childrenTickets) {
                    childrenTickets[_]['invalid'].push(ticket);
                }
            }
            else {
                if (!childrenTickets[ticket.payee])
                    childrenTickets[ticket.payee] = {
                        'valid': [],
                        'invalid': []
                    };

                childrenTickets[ticket.payee]['invalid'].push(ticket);
            }
        }

        return childrenTickets;
    }

    _render_Tickets_UI () {

    }

    updatePrintButton () {
        const link = document.querySelector('#Shop .Controls .Controls-buttons .js-print');
        
        link.classList.remove('d-none');
        link.target = '_blank';
        link.href = '/order/print/' + hp._order.id;
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

    onButtonPreviousClick (e) { window.history.back(); }

    onButtonPayClick (e) {
        Payment.cart = this._cart;
        Payment.amount = this._order.amount - this._order.amount_rcvd;

        Payment.payer.id = this._parent.id;
        Payment.payer.email = this._parent.auth.email;

        Payment.order = {
            id:         (this._order.id) ? this._order.id : 0,
            type:       this._order.type,
            caster:     this._order.caster,
            comment:    this._order.comment,
            reference:  this._order.reference,
        }

        Payment.init(this.payment_status);
    }


    payment_status (status) {
        console.log(status);

        hp._order.id = status.orderID;

        switch (status.reason) {
            case 'Payed':
                Messages().success.write('payment', 'La commande a bien été validée.');
                hp.updatePrintButton();
                break;

            case 'Reserved':
                Messages().success.write('payment', 'La commande a bien été réservée.');
                hp.updatePrintButton();
                break;

            case 'Confirmed':
                Messages().success.write('payment', 'La commande a bien été enregistrée. Elle sera placée EN ATTENTE pendant 30 minutes.');
                break;

            case 'VADS':
                Messages().success.write('payment', 'La commande a bien été enregistrée. Elle sera placée EN ATTENTE pendant 30 minutes le temps que le paiement soit traité.');
                break;

            default:
                console.log('Unknow reason received.' + status.reason);
                break;
        }
    }
}

// const QUOTIENT = [
//     '<i>AUCUN</i>',
//     'NE',
//     'Q2',
//     'Q1',
// ];

// const CLASSROOM = [
//     '<i>AUCUN</i>',
//     'STP',
//     'SP',
//     'SM',
//     'SG',
//     'CP',
//     'CE1',
//     'CE2',
//     'CM1',
//     'CM2',
// ];
