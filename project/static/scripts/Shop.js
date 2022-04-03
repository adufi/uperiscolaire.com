function macro_innerHTML (e, innerHTML) {
    document.querySelectorAll(e).forEach((item) => { item.innerHTML = innerHTML; });
}

class Shop {
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


var _Shop = {

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
var __Shop = {

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

const ___Shop = {

    url_id: 0,
    main_id: 0,

    // parent

    init () {
        this.readIDFromURL();
        if (!this.getMainID()) {
            throw ('Impossible de trouver un ID valide.');
        } 
        return true;


        return new Promise((resolve, reject) => {
            resolve(1);
        })
        .then(() => {
            // this.apiChaining();
        });
    },

    readIDFromURL () {
        const ps = window.location.pathname.split('/');
        if (ps && ps.length) {
            let psx = '';

            if (ps[ps.length - 2]) {
                psx = ps[ps.length - 2];
            }
            else if (ps[ps.length - 1]) {
                psx = ps[ps.length - 1];
            }
            else {
                return;
            }

            if (!(this.url_id = parseInt(psx))) {
                this.url_id = 0;
            }
        }
    },

    getMainID () {
        if (!this.url_id) {
            this.main_id = App.caster.id;
            if (!this.main_id) {
                return false;
            }
        }
        else {
            this.main_id = this.url_id;
        }
        return true;
    },

    apiChaining () {
        if (!this.main_id) {
            Alert.alertDanger('Impossible de trouver un ID valide.');
            return false;
        }

        return new Promise(function (resolve, reject) {
            App.get('/api/params/product/')
            .then((data) => {
                try{
                    console.log(data);
                    schoolYear = data.school_year;
                    productHelper.init(data.products);
                }
                catch (error) {
                    reject(error);
                }
                resolve(1);
            })
            .catch(err => reject(err))
        })
        .then (function (result) {
            return child.readUser(
                child_id,
                (data) => console.log(data),
                (err) => console.log(err)
                // readUser_onSuccess,
                // readUser_onFailure
            );
        })
        .then (function (result) {
            console.log(result);
            return sibling.readByChild(
                child_id,
                (data) => console.log(data),
                (err) => console.log(err)
                // readSibling_onSuccess,
                // readSibling_onFailure
            );
        })
        .then (function (result) {
            console.log(result);
            return records.readByParent(
                sibling._parent,
                (data) => console.log(data),
                (err) => console.log(err)
                // readRecords_onSuccess,
                // readRecords_onFailure
            );
        })
        .then (function (result) {
            console.log(sibling);
            return parent.readUser(
                sibling._parent,
                (data) => console.log(data),
                (err) => console.log(err)
                // readRecords_onSuccess,
                // readRecords_onFailure
            );
        })
        .then ((data) => {
            console.log(data);
            run();
        })
        .catch ((err) => {
            console.log(err);
        })
    },

};