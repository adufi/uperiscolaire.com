const STATUSENUM = {


};


class OrdersInterface {

};


class OrderInterface {

    constructor () {
        this.id = 0;
        
        this.name = ''; // Ignored
        this.comment = '';

        this.date = undefined;

        this.payer = 0;
        this.caster = 0;

        this.reference = '';
        this.type = 1;

        this.amount = 0;
        this.methods = [];

        this.status = [];

        /*
            product: 0
            children: []
        */
        this.cart = [];

        this.tickets = [];
        this.tickets_invalid = [];

        //
        this.TYPE = {
            'OFF': 1,
            'DIR': 2,
            'ONL': 3,
            'MIG': 4,
            'MIG_DIR': 5
        };

        // API vars
        this.verify_response = undefined;
    }


    fromData (data) {
        this.id = getAttr(data, 'id', 0);

        this.type       = getAttr(data, 'type', 1);
        this.reference  = getAttr(data, 'reference', '');

        this.name       = getAttr(data, 'name', '');
        this.comment    = getAttr(data, 'comment', '');

        this.date       = getAttr(data, 'date', '');

        this.caster     = getAttr(data, 'caster', 0);
        this.payer      = getAttr(data, 'payer', 0);

        this.amount     = getAttr(data, 'amount', 0);
        
        this.cart               = getAttr(data, 'cart', []);
        this.tickets            = getAttr(data, 'tickets', []);
        this.tickets_invalid    = getAttr(data, 'tickets_invalid', []);

        this.status     = getAttr(data, 'status', []);
        this.methods    = getAttr(data, 'methods', []);
    }


    fromID (id) {
        const self = this;
        return new Promise((resolve, reject) => {
            App.get(`/api/orders/?pk=${id}`, true)
            .then(data => {
                if (getAttr(data, 'order')) {
                    self.fromData(data.order);
                    resolve(data);
                }
                else {
                    throw 'Impossible de récupérer le payload.';
                }
            })
            .catch(err => {
                console.error(err);
                reject(err);
            });
        })
    }


    //
    // LOGICS
    //

    refresh () {
        if (this.id) {
            return this.fromID(this.id);
        }
        return false;
    }


    //
    // API
    //

    cancelOrder () {
        return App.post(`/api/order/cancel/`, JSON.stringify({
            'client': this.payer,
            'order_id': this.id
        }), true);
    }


    cancelTickets (ticketsSelected) {
        if (ticketsSelected.length) {
            return App.post(`/api/tickets/cancel/`, JSON.stringify({
                'client': this.payer,
                'tickets': ticketsSelected
            }), true);
        }

        return false; 
    }


    // OLD


    // Init class from Shop Summary 
    fromSummary (_order) {
        this.comment = _order['comment'];
        this.reference = _order['reference'];
        
        this.caster = _order['caster'];
        this.payer = _order['payer'];
        
        // this.peri = _order['peri'];
        // this.alsh = _order['alsh'];
        this.cart = _order['cart'];
        
        this.type = this.TYPE[_order['type']];
    }


    // Init class from local storage 
    fromLocalStorage (_order) {
        this.comment = _order['comment'];
        this.reference = _order['reference'];
        
        this.caster = _order['caster'];
        this.payer = _order['payer'];
        
        // this.peri = _order['peri'];
        // this.alsh = _order['alsh'];
        this.cart = _order['cart'];
        
        this.type = this.TYPE[_order['type']];

        this.amount = _order.amount;
    }


    fromAPI (_order) {
        this.id = _order.id;

        this.type = _order.type;
        this.reference = _order.reference;

        this.name = _order.name;
        this.comment = _order.comment;

        this.date = _order.date;

        this.caster = _order.caster;
        this.payer = _order.payer;

        this.amount = _order.amount;
        
        this.status = _order.status;
        this.methods = _order.methods;
        this.tickets = _order.tickets;
    }


    toLocalStorage () {
        return JSON.stringify({
            'name': this.name,
            'comment': this.comment,

            'amount': this.amount,
            
            'caster': this.caster,
            'payer': this.payer,
            
            // 'alsh': this.alsh,
            'cart': this.cart,
            // 'peri': this.peri,

            'type': this.type,
            'reference': this.reference,
        })
    }




    /**
     * SETTERS
     */

    setPayer (payer) {
        this.payer = payer;
    }

    setCaster (caster) { this.caster = caster; }

    setType (type) {
        if (!this.TYPE[type]) {
            return false;
        }
        this.type = this.TYPE[type];
        return true;
    }

    setReference (ref) { this.reference = ref; }

    setMethods (methods) { this.methods = methods; }


    payload () {
        if (this.peri.length ||
            this.alsh.length) {
            
            const payload = {
                'name': this.name,
                'comment': this.comment,
    
                'payer': this.payer,
                'caster': this.caster,
    
                'reference': this.reference,
                'type': this.type,
    
                // 'peri': this.peri,
                // 'alsh': this.alsh,
                'cart': this.cart,
            };
    
            if (this.id)
                payload['id'] = this.id;
            return payload;
        }

        return false;
    }


    /**
     * API
     */

    getOrder (id, onSuccess, onFailure) {
        App.get(
            '/api/order/' + id
        )
            .then((data) => {
                console.log(data);

                this.get_onSuccess (data);

                if (onSuccess)
                    onSuccess(data);
            })
            .catch((err) => {
                console.log(err);

                this.get_onFailure (err);
            
                if (onFailure)
                    onFailure(err);
            });

        return true;
    }


    verify (onSuccess, onFailure) {
        let self = this;
        if (!this.payer && !this.caster)
            return false;

        if (!this.cart.length) {
            return false;
        }

        App.post(
            '/api/order/verify/',
            JSON.stringify({
                'payer': this.payer,
                'caster': this.caster,

                // 'peri': this.peri,
                // 'alsh': this.alsh,
                'cart': this.cart,
            }), 
            true
        )
            .then((data) => {
                console.log(data);

                this.verify_onSuccess (data);

                if (onSuccess)
                    onSuccess(data);
            })
            .catch((err) => {
                console.log(err);

                this.verify_response = err;
            
                if (onFailure)
                    onFailure(err);
            });

        return true;
    }


    pay (onSuccess, onFailure) {
        if (!this.payer && !this.caster)
            return false;

        if (!this.cart.length) {
            return false;
        }

        App.post(
            '/api/order/pay/',
            JSON.stringify({
                'name': this.name,
                'comment': this.comment,

                'payer': this.payer,
                'caster': this.caster,

                'type': this.type,
                'reference': this.reference,

                'methods': this.methods,

                // 'peri': this.peri,
                // 'alsh': this.alsh,
                'cart': this.cart,
            }),
            true
        )
        .then((data) => {
            console.log (data);
            if (onSuccess)
                onSuccess(data);
        })
        .catch((err) => {
            console.log (err);
            if (onFailure)
                onFailure(err);
        });

        return true;
    }


    reserve (onSuccess, onFailure) {
        if (!this.payer && !this.caster)
            return false;

        if (!this.cart.length) {
            return false;
        }

        App.post(
            '/api/order/reserve/',
            JSON.stringify({
                'name': this.name,
                'comment': this.comment,

                'payer': this.payer,
                'caster': this.caster,

                'type': this.type,
                'reference': this.reference,

                // 'peri': this.peri,
                // 'alsh': this.alsh,
                'cart': this.cart 
            })
        )
        .then((data) => {
            console.log (data);
            if (onSuccess)
                onSuccess(data);
        })
        .catch((err) => {
            console.log (err);
            if (onFailure)
                onFailure(err);
        });

        return true;
    }


    /**
     * API Handler
     */
    get_onSuccess (data) {
        this.fromAPI(data['order']);
    }

    get_onFailure (err) {}
    

    verify_onSuccess (data) {

        this.amount = data['amount'];
        this.tickets = data['tickets'];
        this.tickets_invalid = data['tickets_invalid'];

        if (data['tickets_invalid']) {

            data['tickets_invalid'].forEach((ticket) => {

                this.removeProduct(ticket['payee'], ticket['child']);
            });
        }
    }

    verify_onFailure (err) {}


    // Remove a product from PERI/ALSH list
    removeProduct (child, product) {
        // CART
        for (let i = 0; i < this.cart.length; ++i) {

            if (this.cart[i]['product'] === product) {

                let found = this.cart[i]['children'].indexOf(child)

                if (found !== -1) {
                    this.cart[i]['children'].splice(found, 1);

                    // If item is empty
                    if (!this.cart[i]['children'].length) {
                        this.cart.splice(i, 1);
                    }

                    return true;
                }

                return false;
            } 
        }
        return false;
        
        // PERI
        for (let i = 0; i < this.peri.length; ++i) {

            if (this.peri[i]['product'] === product) {

                let found = this.peri[i]['children'].indexOf(child)

                if (found !== -1) {
                    this.peri[i]['children'].splice(found, 1);

                    // If item is empty
                    if (!this.peri[i]['children'].length) {
                        this.peri.splice(i, 1);
                    }

                    return true;
                }

                return false;
            } 
        }

        // ALSH
        for (let i = 0; i < this.alsh.length; ++i) {

            if (this.alsh[i]['child'] === child) {

                let found = this.alsh[i]['products'].indexOf(product)

                if (found !== -1) {
                    this.alsh[i]['products'].splice(found, 1);

                    // If item is empty
                    if (!this.alsh[i]['products'].length) {
                        this.alsh.splice(i, 1);
                    }

                    return true;
                }

                return false;
            } 
        }

        return false;
    }


    print () {
        
    }
    
};


class UI_OrderModal {

    constructor () {
        this.ORDERTYPES = [
            '<i>Inconnu</i>',
            'ANTENNE',
            'DIRECTRICE',
            'EN LIGNE',
            'MIGRATION',
            'MIGRATION DIR.'
        ];
        
        this.METHODTYPES = [
            '<i>Inconnu</i>',
            'ESPECES',
            'CHEQUE',
            'EN LIGNE',
            'VIRMENT',
            'AVOIR',
            'PAYPAL',
            'STRIPE',
        ];

        this.STATUSLABELS = [
            '<a class="ui black label">Inconnu</a>',
            '<a class="ui olive label">Réservé</a>',
            '<a class="ui green label">Payé</a>',
            '<a class="ui grey label">Reporté</a>',
            '<a class="ui blue label">Remboursé</a>',
            '<a class="ui red label">Annulé</a>',
            '<a class="ui yellow label">En attente</a>',
            '<a class="ui teal label">Crédité</a>',
        ];

        this.CLASSROOMS = [
            '<i>Aucune classe</i>',
            'STP',
            'SP',
            'SM',
            'SG',
            'CP',
            'CE1',
            'CE2',
            'CM1',
            'CM2',
            'AUTRES',
        ];

        this.QUOTIENT = [
            '<i>Aucun quotient</i>',
            'NE',
            'Q2',
            'Q1',
        ];
    }


    //
    // LOGICS
    //

    render (Order) {
        this._main = document.querySelector('.Order.Order-Modal');
        if (!this._main) {
            console.error('Failed to get main element.');
            return false;
        }

        // Initialization
        
        console.log(Order);
        this._Order = Order;

        // Family data
        this._family = {
            'parent': {},
            'children': {},
            'intel': {},
            'records': []
        };

        // Tickets selected for cancelation
        this._tickets_selected = [];

        this.clear();
        
        $(this._main).modal('show');
        // $('.ui.longer.modal').modal('show');

        this.renderModal();

        const self = this;

        this._main.querySelector('.js-modal-close').onclick = (e) => self.close();
        this._main.querySelector('.js-modal-print').onclick = (e) => self.print();
        this._main.querySelector('.js-modal-cancel-order').onclick = (e) => self.cancelOrder();
        this._main.querySelector('.js-modal-cancel-tickets').onclick = (e) => self.cancelTickets();
    }


    /**
     * 
     */
    updateSelectedTickets (id) {
        const tile = document.querySelector(`.product-tile[data-ticket="${id}"]`);
        if (!tile) {
            return false;
        }
        
        let index = -1;
        if ((index = this._tickets_selected.indexOf(id)) >= 0) {
            tile.classList.remove('selected');
            this._tickets_selected.splice(index, 1);
        }
        else {
            tile.classList.add('selected');
            this._tickets_selected.push(id);
        }

        // Update UI
        document.querySelector('.js-modal-selected').innerHTML = this._tickets_selected.length + ` ticket(s) sélectionné(s)`;

        if (this._tickets_selected.length) {
            document.querySelector('.js-modal-cancel-tickets').classList.remove('d-none');
        }
        else {
            document.querySelector('.js-modal-cancel-tickets').classList.add('d-none');
        }

        return true;
    }


    print () {
        if (this._Order && this._Order.id)
            window.open(`/order/print/${this._Order.id}`);
    }


    refresh () {
        const self = this;
        this._Order.refresh()
        .then(() => {
            try {
                self.render(this._Order);
            }
            catch (error) {
                console.error(error);
            }
        })
        .catch(err => {
            console.error(err);
        });
    }


    close () {
        if (this._tickets_selected.length) {

            const choice = confirm(`Etes-vous sûr de vouloir quitter, ${this._tickets_selected.length} ticket(s) sélectionné(s) ?`);

            if (choice) {
                $('.js-modal').modal('hide');
                // $('.ui.longer.modal').modal('hide');
            }
        }
    }


    cancelOrder () {
        const self = this;
        const choice = confirm(`Etes-vous sûr de vouloir annuler ce reçu ?`);
        
        if (choice) {
            return this._Order.cancelOrder()
            .then(data => self.cancel_onSuccess(data))
            .catch(err => self.cancel_onFailure(err));
        }
        return false;
    }


    cancelTickets () {
        if (this._tickets_selected.length) {

            const self = this;
            const choice = confirm(`Etes-vous sûr de vouloir annuler ${this._tickets_selected.length} ticket(s) ?`);

            if (choice) {
                return this._Order.cancelTickets(this._tickets_selected)
                .then(data => self.cancel_onSuccess(data))
                .catch(err => self.cancel_onFailure(err));
            }
        }
        return false;
    }


    cancel_onSuccess (data) {
        this.refresh();
        console.log(data.cancel_status);
        alert(data.cancel_status);
    }


    cancel_onFailure (err) {
        console.error(err);
    }


    // UI & RENDERING
    // ...
    //

    // Clear HTML items in modal
    clear () {    

        // 
        this._main.querySelector('.js-modal-selected').innerHTML = '0 ticket sélectionné';

        // Clear methods
        this._main.querySelectorAll('.js-modal-methods .ui.small.feed.row').forEach(item => item.remove());

        // Clear status
        this._main.querySelectorAll('.js-modal-status .ui.small.feed.row').forEach(item => item.remove());

        // Clear children
        this._main.querySelectorAll('.js-modal-child').forEach(item => item.remove());

        this._main.querySelector('.js-modal-cancel-tickets').classList.add('d-none');
    }


    /**
     * Fill modal with order/user data
     */
    renderModal () {
        try {
            const main = this._main;
            const Order = this._Order;
            
            // ID & Name
            main.querySelector('.js-modal-id').innerHTML = Order.id;
            main.querySelector('.js-modal-name').innerHTML = Order.name;

            // Order status
            const status = Order.status[0].status;
            main.querySelector('.js-modal-last-status').innerHTML = this.STATUSLABELS[status];

            // Date
            const date = Order.status[0].date;
            main.querySelector('.js-modal-date').innerHTML = _datetime(date);

            // Ref
            main.querySelector('.js-modal-ref').innerHTML = Order.reference;

            // Comment
            main.querySelector('.js-modal-comment').innerHTML = Order.comment;

            // Type
            main.querySelector('.js-modal-type').innerHTML = this.ORDERTYPES[Order.type];

            // Amount
            main.querySelector('.js-modal-amount').innerHTML = Order.amount;

            // Methods
            const modal_methods = main.querySelector('.js-modal-methods');
            for (const method of Order.methods) {
                const xref = (ref) => { return (ref) ? ref : '<i>Aucune référence</i>'; }

                modal_methods.innerHTML += `
                <div class="ui small feed row">
                    <p class="col-12 col-sm-3"><b>Type:</b>         <span>${this.METHODTYPES[method.method]}</span></p>
                    <p class="col-12 col-sm-3"><b>Montant:</b>      <span>${method.amount}</span> €</p>
                    <p class="col-12 col-sm-3"><b>Référence:</b>    <span>${xref(method.reference)}</span></p>
                </div>`;
            }

            // Status
            const modal_status = main.querySelector('.js-modal-status');
            for (const status of Order.status) {
                modal_status.innerHTML += `
                <div class="ui small feed row">
                    <p class="col-12 col-sm-3"><b>Status:</b>       <span>${this.STATUSLABELS[status.status]}</span></p>
                    <p class="col-12 col-sm-3"><b>Date:</b>         <span>${_datetime(status.date)}</span></p>
                </div>`;
            }
            
            // Tickets
            const children = {};
            const modal_children = main.querySelector('.js-modal-children');

            // Order tickets
            for (const ticket of Order.tickets) {
                if (!children[ticket.payee]) {
                    children[ticket.payee] = [];
                }

                children[ticket.payee].push(ticket);
            }

            console.log(children);

            for (const id of Object.keys(children)) {
                const products = document.createElement('div');
                products.className = 'products';

                for (const ticket of children[id]) {
                    const product = productHelper.get(ticket.product);
                    if (product) {
                        const tile = productHelper.render('order-modal', product, id);
                        
                        // Ticket status
                        const date = ticket.status[0].date;
                        const status = ticket.status[0].status;

                        tile.querySelector('.product-meta-price').innerHTML = `${ticket.price} €`;
                        tile.querySelector('.product-meta-bought').innerHTML = `${this.STATUSLABELS[status]} le ${_date(date)}`;                  

                        tile.setAttribute('data-ticket', ticket.id);
                        
                        products.appendChild(tile);
                    }
                }

                modal_children.innerHTML += `
                <div class="content js-modal-child" data-child="${id}">
                    <h4 class="ui sub header">
                        <span class="js-modal-names"></span> - 
                        <span class="js-modal-dob"></span> - 
                        <span class="js-modal-classroom"></span></h4>
                    <div class="ui small feed row">
                        <div class="products">${products.innerHTML}</div>
                    </div>
                </div>`;
            }

            const self = this;

            main.querySelectorAll('.product-tile').forEach((tile) => {
                tile.onclick = function (e) {
                    self.ticket_onClick(this);
                };
            });

            this.readFamily();
        }
        catch (error) {
            console.error(error);
        }
    }


    /**
     *  Update modal with family details
     */
    updateFamily () {
        const main = this._main;
        const parent = this._family.parent;

        main.querySelector('.js-modal-payer').innerHTML = `${parent.first_name} ${parent.last_name}`;

        // Quotients
        main.querySelector('.js-modal-quotient-1').innerHTML = this.QUOTIENT[this._family.intel.quotient_1];
        main.querySelector('.js-modal-quotient-2').innerHTML = this.QUOTIENT[this._family.intel.quotient_2];
        
        // Update children
        main.querySelectorAll('.content.js-modal-child').forEach(item => {
            const id = parseInt(item.getAttribute('data-child'));
            if (id) {
                let dob = '<i>Pas de date de naissance</>';
                let names = '<i>Aucun nom trouvé</>';

                for (const child of this._family.children) {
                    if (child.id === id) {
                        dob = child.dob;
                        names = `${child.first_name} ${child.last_name}`;
                        break;
                    }
                }

                item.querySelector('.js-modal-dob').innerHTML = dob;
                item.querySelector('.js-modal-names').innerHTML = names;

                let classroom = '<i>Aucune classe</i>';
                for (const record of this._family.records) {
                    if (record.child === id) {
                        classroom = this.CLASSROOMS[record.classroom];
                        break;
                    }
                }

                item.querySelector('.js-modal-classroom').innerHTML = classroom;
            }
        });
    }


    /**
     *  EVENTS
     */

    ticket_onClick (target) {
        const id = parseInt(target.getAttribute('data-ticket'));
        console.log(id);
        if (id) {
            this.updateSelectedTickets(id);
        }
    }


    close_onClick () { this.close(); }

    /**
     *  API
     */


    /**
     *  Get family details
     *  - Parent
     *  - Sibling (children + intels)
     *  - Records
     */
    readFamily () {
        const self = this;

        // Get active school year
        let schoolYear = {};
        for (const s of App.schoolYears) if (s.is_active) { schoolYear = s; break; }

        return new Promise(function (resolve, reject) {

            // Get parent
            App.get(`/api/user/${self._Order.payer}/`, true)
            .then((data) => resolve(data))
            .catch((err) => reject(err));
        })
        .then (function (result) {
            // Parent
            console.log(result);
            self._family.parent = result.user;

            return App.get(`/api/sibling/?parent=${self._Order.payer}`, true);
        })
        .then (function (result) {
            // Sibling
            console.log(result);

            for (const _ of result.sibling.intels) {
                if (_.school_year === schoolYear.id) {
                    self._family.intel = _;
                    break;
                }
            }
            
            self._family.children = result.sibling.children;

            return App.get(`/api/record/?parent=${self._Order.payer}`, true);
        })
        // .then (function (result) {
        //     console.log(sibling);
        //     return parent.readUser(
        //         sibling._parent,
        //         (data) => console.log(data),
        //         (err) => console.log(err)
        //         // readRecords_onSuccess,
        //         // readRecords_onFailure
        //     );
        // })
        // .then (function (result) {
        //     return App.get(`/api/order/?payer=${parent.id}`, true)
        //         .then((data) => {
        //             console.log(data);
        //             orders = data.orders;
        //         })
        //         .catch((err) => console.log(err));
        // })
        .then ((data) => {
            // Records
            console.log(data);

            for (const _ of data.records) {
                if (_.school_year === schoolYear.id) {
                    self._family.records.push(_);
                    break;
                }
            }

            self.updateFamily();
        })
        .catch ((err) => {
            console.log(err);
        });
    }

};


class UI_OrderPrint {

    constructor () {
        this.ORDERTYPES = [
            '<i>Inconnu</i>',
            'ANTENNE',
            'DIRECTRICE',
            'EN LIGNE',
            'MIGRATION',
            'MIGRATION DIR.'
        ];
        
        this.METHODTYPES = [
            '<i>Inconnu</i>',
            'ESPECES',
            'CHEQUE',
            'EN LIGNE',
            'VIRMENT',
            'AVOIR',
            'PAYPAL',
            'STRIPE',
        ];

        this.STATUSLABELS = [
            'INCONNU',
            'RESERVE',
            'PAYE',
            'REPORTE',
            'REMBOURSE',
            'ANNULE',
            'EN ATTENTE',
            'CREDITE',
        ];

        this.CLASSROOMS = [
            '<i>Aucune classe</i>',
            'STP',
            'SP',
            'SM',
            'SG',
            'CP',
            'CE1',
            'CE2',
            'CM1',
            'CM2',
            'AUTRES',
        ];

        this.QUOTIENT = [
            'NE',
            'NE',
            'Q2',
            'Q1',
        ];
    }


    //
    // LOGICS
    //

    render (Order) {
        this._main = document.querySelector('.Order.Order-Print');
        if (!this._main) {
            console.error('Failed to get main element.');
            return false;
        }

        // Initialization
        
        console.log(Order);
        this._Order = Order;

        // Family data
        this._family = {
            'parent': {},
            'children': {},
            'intel': {},
            'records': []
        };

        // Tickets selected for cancelation
        this._tickets_selected = [];

        this._alteredDict = {
            'x-peri-1':     {'price': 20, 'qtty': 0},
            'x-peri-2':     {'price': 32, 'qtty': 0},
            'x-peri-3':     {'price': 40, 'qtty': 0},
            'x-peri-4':     {'price': 60, 'qtty': 0},
    
            'x-xtra-m-ne':  {'price': 17, 'qtty': 0},
            'x-xtra-m-q2':  {'price': 4, 'qtty': 0},
            'x-xtra-m-q1':  {'price': 0, 'qtty': 0},
    
            'x-xtra-p-ne':  {'price': 20, 'qtty': 0},
            'x-xtra-p-q2':  {'price': 7, 'qtty': 0},
            'x-xtra-p-q1':  {'price': 2, 'qtty': 0}
        };

        // Clear UI
        this.clear();
        
        // $(this._main).modal('show');
        // $('.ui.longer.modal').modal('show');

        // Not a modal actually
        this.renderModal();

        // const self = this;
        // this._main.querySelector('.js-modal-close').onclick = () => self.close();
    }


    refresh () {
        const self = this;
        this._Order.refresh()
        .then(() => {
            try {
                self.render(this._Order);
            }
            catch (error) {
                console.error(error);
            }
        })
        .catch(err => {
            console.error(err);
        });
    }


    close () {
        if (this._tickets_selected.length) {

            const choice = confirm(`Etes-vous sûr de vouloir quitter, ${this._tickets_selected.length} ticket(s) sélectionné(s) ?`);

            if (choice) {
                $('.js-modal').modal('hide');
                // $('.ui.longer.modal').modal('hide');
            }
        }
    }


    // UI & RENDERING
    // ...
    //

    // Clear HTML items in modal
    clear () {

        // Clear methods
        this._main.querySelector('.js-modal-methods table tbody').innerHTML = '';
        
        // Clear status
        this._main.querySelector('.js-modal-status table tbody').innerHTML = '';

        // Clear children
        this._main.querySelectorAll('.js-modal-child').forEach(item => item.remove());
    }


    /**
     * Fill modal with order/user data
     */
    renderModal () {
        try {
            const main = this._main;
            const Order = this._Order;
            
            // ID & Name
            main.querySelector('.js-modal-id').innerHTML = Order.id;
            // main.querySelector('.js-modal-name').innerHTML = Order.name;

            // Order status
            const status = Order.status[0].status;
            main.querySelector('.js-modal-last-status span').innerHTML = this.STATUSLABELS[status];

            // Date
            const date = Order.status[0].date;
            main.querySelector('.js-modal-date').innerHTML = _datetime(date);

            // Ref
            main.querySelector('.js-modal-ref').innerHTML = Order.reference;

            // Comment
            main.querySelector('.js-modal-comment').innerHTML = Order.comment;

            // Type
            main.querySelector('.js-modal-type').innerHTML = this.ORDERTYPES[Order.type];

            // Amount
            main.querySelector('.js-modal-amount').innerHTML = Order.amount;

            // Methods
            const modal_methods = main.querySelector('.js-modal-methods table tbody');
            for (const method of Order.methods) {
                const xref = (ref) => { return (ref) ? ref : '<i>Aucune référence</i>'; }

                modal_methods.innerHTML += `
                <tr class="ui small feed">
                    <td data-label="Type">      ${this.METHODTYPES[method.method]}</td>
                    <td data-label="Amount">    ${method.amount} €</td>
                    <td data-label="Reference"> ${xref(method.reference)}</td>
                </tr>`;
            }

            // Status
            const modal_status = main.querySelector('.js-modal-status table tbody');
            for (const status of Order.status) {
                modal_status.innerHTML += `
                <tr class="ui small feed">
                    <td data-label="Status">    ${this.STATUSLABELS[status.status]}</td>
                    <td data-label="Date">      ${_datetime(status.date)}</td>
                </tr>`;
            }
            
            // Tickets
            const children = {}; // children { 'child_id': [tickets] }
            const modal_children = main.querySelector('.js-modal-children');

            // Order tickets by child
            for (const ticket of Order.tickets) {
                if (!children[ticket.payee]) {
                    children[ticket.payee] = [];
                }

                children[ticket.payee].push(ticket);
            }

            console.log(children);

            for (const id of Object.keys(children)) {
                const products = document.createElement('div');
                products.className = 'products';

                for (const ticket of children[id]) {
                    const product = productHelper.get(ticket.product);
                    if (product) {
                        const tile = productHelper.render('order-modal', product, id);
                       
                        // Ticket status
                        const date = ticket.status[0].date;
                        const status = ticket.status[0].status;
                        
                        tile.querySelector('.product-meta-price').innerHTML = this.alterPrice(ticket.price, product.category);
                        if (status === 2) {
                            tile.querySelector('.product-meta-bought').remove();                  
                        }
                        else {
                            tile.querySelector('.product-meta-bought').innerHTML = `${this.STATUSLABELS[status]} le ${_date(date)}`;                  
                        }

                        tile.setAttribute('data-ticket', ticket.id);
                        
                        products.appendChild(tile);
                    }
                }

                modal_children.innerHTML += `
                <div class="content js-modal-child" data-child="${id}">
                    <h4 class="ui sub header">
                        <span class="js-modal-names"></span> - 
                        <span class="js-modal-dob"></span> - 
                        <span class="js-modal-classroom"></span></h4>
                    <div class="ui small feed row">
                        <div class="products">${products.innerHTML}</div>
                    </div>
                </div>`;
            }

            const self = this;

            this.readFamily();
            this.applyAlters();
        }
        catch (error) {
            console.error(error);
        }
    }


    alterPrice (price, category) {
        // console.log(price);
        // console.log(typeof(price));

        switch (price) {
            case 20:
                if (category === 1) {
                    this._alteredDict['x-peri-1'].qtty++;
                    return 'PERI-1';
                }
                else {
                    this._alteredDict['x-xtra-p-ne'].qtty++;
                    return 'XTRA-P-NE';
                }
                
            case 16:
                this._alteredDict['x-peri-2'].qtty++;
                return 'PERI-2';
                
            case 13.333333333333334:
                this._alteredDict['x-peri-3'].qtty++;
                return 'PERI-3';

            case 15:
                this._alteredDict['x-peri-4'].qtty++;
                return 'PERI-4';

            case 0:
                this._alteredDict['x-xtra-m-q1'].qtty++;
                return 'XTRA-M-Q1';

            case 4:
                this._alteredDict['x-xtra-m-q2'].qtty++;
                return 'XTRA-M-Q2';

            case 17:
                this._alteredDict['x-xtra-m-ne'].qtty++;
                return 'XTRA-M-NE';

            case 2:
                this._alteredDict['x-xtra-p-q1'].qtty++;
                return 'XTRA-P-Q1';

            case 7:
                this._alteredDict['x-xtra-p-q2'].qtty++;
                return 'XTRA-P-Q2';            
        }
    }


    applyAlters () {
        this._alteredDict['x-peri-2'].qtty /= 2;
        this._alteredDict['x-peri-3'].qtty /= 3;
        this._alteredDict['x-peri-4'].qtty /= 4;

        const main = this._main.querySelector('.js-modal-lexique');

        Object.keys(this._alteredDict).forEach((key) => {
            const x = this._alteredDict[key];

            if (x.qtty) {
                const row = main.querySelector('.' + key);
    
                row.classList.add('show');

                row.querySelector('.x-qtty').innerHTML = x.qtty;
                row.querySelector('.x-unit').innerHTML = x.price;
                row.querySelector('.x-sum').innerHTML = (x.qtty * x.price);
            }
        });
    }


    /**
     *  Update modal with family details
     */
    updateFamily () {
        const main = this._main;
        const parent = this._family.parent;

        main.querySelector('.js-modal-payer').innerHTML = `${parent.first_name} ${parent.last_name}`;

        // Quotients
        main.querySelector('.js-modal-quotients').innerHTML = 
            `${this.QUOTIENT[this._family.intel.quotient_1]}/${this.QUOTIENT[this._family.intel.quotient_2]}`;
        
        // Update children
        main.querySelectorAll('.content.js-modal-child').forEach(item => {
            const id = parseInt(item.getAttribute('data-child'));
            if (id) {
                let dob = '<i>Pas de date de naissance</>';
                let names = '<i>Aucun nom trouvé</>';

                for (const child of this._family.children) {
                    if (child.id === id) {
                        dob = child.dob;
                        names = `${child.first_name} ${child.last_name}`;
                        break;
                    }
                }

                item.querySelector('.js-modal-dob').innerHTML = dob;
                item.querySelector('.js-modal-names').innerHTML = names;

                let classroom = '<i>Aucune classe</i>';
                for (const record of this._family.records) {
                    if (record.child === id) {
                        classroom = this.CLASSROOMS[record.classroom];
                        break;
                    }
                }

                item.querySelector('.js-modal-classroom').innerHTML = classroom;
            }
        });
    }


    /**
     *  EVENTS
     */


    close_onClick () { this.close(); }

    /**
     *  API
     */


    /**
     *  Get family details
     *  - Parent
     *  - Sibling (children + intels)
     *  - Records
     */
    readFamily () {
        const self = this;

        // Get active school year
        let schoolYear = {};
        for (const s of App.schoolYears) if (s.is_active) { schoolYear = s; break; }

        return new Promise(function (resolve, reject) {

            // Get parent
            App.get(`/api/user/${self._Order.payer}/`, true)
            .then((data) => resolve(data))
            .catch((err) => reject(err));
        })
        .then (function (result) {
            // Parent
            console.log(result);
            self._family.parent = result.user;

            return App.get(`/api/sibling/?parent=${self._Order.payer}`, true);
        })
        .then (function (result) {
            // Sibling
            console.log(result);

            for (const _ of result.sibling.intels) {
                if (_.school_year === schoolYear.id) {
                    self._family.intel = _;
                    break;
                }
            }
            
            self._family.children = result.sibling.children;

            return App.get(`/api/record/?parent=${self._Order.payer}`, true);
        })
        // .then (function (result) {
        //     console.log(sibling);
        //     return parent.readUser(
        //         sibling._parent,
        //         (data) => console.log(data),
        //         (err) => console.log(err)
        //         // readRecords_onSuccess,
        //         // readRecords_onFailure
        //     );
        // })
        // .then (function (result) {
        //     return App.get(`/api/order/?payer=${parent.id}`, true)
        //         .then((data) => {
        //             console.log(data);
        //             orders = data.orders;
        //         })
        //         .catch((err) => console.log(err));
        // })
        .then ((data) => {
            // Records
            console.log(data);

            for (const _ of data.records) {
                if (_.school_year === schoolYear.id) {
                    self._family.records.push(_);
                    break;
                }
            }

            self.updateFamily();
        })
        .catch ((err) => {
            console.log(err);
        });
    }

};


const Encaissements = {

    products: {},


    render (data) {
        const rows = [];
    },


    orderByChild (orders) {
        const children = [
            // id
            // tickets
        ];
        
        for (const order of orders) {

            const children_tickets = {};

            for (const ticket of order.tickets) {
                
                if (!children_tickets[ticket.payee]) {
                    children_tickets[ticket.payee] = [];
                }

                children_tickets[ticket.payee].push(ticket);
            }

            for (const child_tickets of Object.keys(children_tickets)) {

                let found = false;
                for (const child of children) {
                    if (child_tickets === child.id) {

                        child.tickets = child.tickets.concat(children_tickets[child_tickets]);
                        found = true;
                    }
                }

                if (!found) {
                    children.push({
                        id: child_tickets,
                        tickets: children_tickets[child_tickets]
                    });
                }
            }
        }

        const raw_rows = this.orderByCategory(children);
    },


    orderByCategory (children) {
        const rows = [
            // Child ID
            // Amount cash
            // Amount check
            // Amount credit
        ];

        for (const child of children) {

            const peri = {};
            const alsh = {};

            for (const ticket of child.tickets) {

                const p = this.products[ticket];
                if (!p) continue;

                
            }
        }
    }
};


class _Order {

    constructor() {
        this.id = 0;

        this.name = ''; // Ignored
        this.comment = '';

        this.payer = 0;
        this.caster = 0;

        this.reference = '';
        this.type = 1;

        /*
            product: 0
            children: []
        */
        this.peri = [];

        /*
            child: 0
            products: []
        */
        this.alsh = [];

        //
        this.TYPE = {
            'OFF': 1,
            'DIR': 2,
            'ONL': 3,
            'MIG': 4,
            'MIG_DIR': 5
        };
    }


    setPayer(payer) {
        this.payer = payer;
    }


    setCaster(caster) { this.caster = caster; }


    setType(type) {
        if (!this.TYPE[type]) {
            return false;
        }
        this.type = this.TYPE[type];
        return true;
    }


    setReference(ref) { this.reference = ref; }


    togglePeri(product, child) {
        // Cart lookup
        for (var i = 0; i < this.peri.length; ++i) {
            const month = this.peri[i];

            // If product exist
            // Check child is in
            if (month['product'] === product) {

                let index = -1;

                // if child not in - add him
                if ((index = month['children'].indexOf(child)) === -1) {
                    month['children'].push(child);
                    return true;
                }

                // If child is in - remove him
                else {
                    month['children'].splice(index, 1);

                    // if children list is empty remove it
                    if (!month['children'].length)
                        this.peri.splice(i, 1);

                    return false;
                }
            }
        }

        // if cart was not found
        this.peri.push({
            'product': product,
            'children': [child]
        });

        return true;
    }


    toggleAlsh(product, child) {
        // Cart lookup
        for (var i = 0; i < this.alsh.length; ++i) {

            // If product exist
            // Check child is in
            if (this.alsh[i]['child'] === child) {

                let index = -1;

                // if child not in - add him
                if ((index = this.alsh[i]['products'].indexOf(product)) === -1) {
                    this.alsh[i]['products'].push(product);
                    return true;
                }

                // if product is in - remove him
                else {
                    this.alsh[i]['products'].splice(index, 1);

                    // if products list is empty remove it
                    if (!this.alsh[i]['products'].length)
                        this.alsh.splice(i, 1);

                    return false;
                }
            }
        }

        // if cart was not found
        this.alsh.push({
            'child': child,
            'products': [product]
        });

        return true;
    }


    payload() {
        if (this.peri.length ||
            this.alsh.length) {

            const payload = {
                'name': this.name,
                'comment': this.comment,

                'payer': this.payer,
                'caster': this.caster,

                'reference': this.reference,
                'type': this.type,

                'peri': this.peri,
                'alsh': this.alsh,
            };

            if (this.id)
                payload['id'] = this.id;
            return payload;
        }

        return false;
    }


    create() {
        $.ajax({
            url: '/intern/orders/create',
            method: 'POST',
            data: {
                'name': this.name,
                'comment': this.comment,

                'payer': this.payer,
                'caster': this.caster,

                'type': this.type,
                'reference': this.reference,

                'peri': this.peri,
                'alsh': this.alsh,
            },
            success(data) {
                console.log(data);
            },
            error(err) {
                response = JSON.parse(err.responseText);
                console.log(response);
            }
        })
    }
};