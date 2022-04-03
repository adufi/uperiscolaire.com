// for test purpose
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

const Payment = {

    VADS_BASE_LINK: 'https://paiement.systempay.fr/vads-site/UNION_DES_PARENTS_D__ELEVES_ET',
    
    amount: 0,
    credit: 0,

    cart: [],

    payer: {
        id: 0, 
        email: ''
    },

    order: {
        id:         0,
        type:       0,
        caster:     0,
        comment:    '',
        reference:  '',
    },    
    
    // UI & HTML
    modal: document.querySelector('.ui.modal.payment.methods'),
    direct_inputs: {
        'cash_amount': document.querySelector('.ui.modal.methods .cash.amount'),
    
        'check_amount': document.querySelector('.ui.modal.methods .check.amount'),
        'check_ref': document.querySelector('.ui.modal.methods .check.ref'),
    },

    summary_cb: undefined,

    // Release 1.0.4
    apiReady: true,
    
    /**
     * 
     * @param {*} param0 
     * 
     * @states
     *  @state1 Admin - New - 
     *  @state2 Admin - Save - 
     *  @state3 Parent - New - 
     *  @state4 Parent - Save - 
     */
    
    init (summary_cb) {

        $('.ui.modal').modal('show');

        if (App.caster.isAdmin) {
            if (this.order.id) this.state2();
            else this.state1();
        }
        else {
            if (this.order.id) this.state4();
            else this.state3();
        }

        this.summary_cb = summary_cb;

        return;

        const modal = document.querySelector('.ui.modal.payment.methods');
    
        if (amount) {
            modal.querySelector('.header.free').classList.add('d-none');
            
            if (credit) {
                modal.querySelector('.credit .value').innerHTML = credit;
            }
            else {
                modal.querySelector('.credit').classList.add('d-none');
            }
    
            modal.querySelector('.amount .value').innerHTML = amount;
        }
        // Free order
        else {
            modal.querySelector('.header.details').classList.add('d-none');
        }
    
        modal.querySelector('.actions .button.positive')
        .addEventListener('click', () => payment_pay_direct());
    
        $('.ui.modal').modal('show');
    },

    reset () {
        this.modal.querySelectorAll('.d-none')
        .forEach(item => item.classList.remove('d-none'));

        this.modal.querySelector('.ui.styled.fluid.accordion')
        .classList.add('d-none');
    },

    // State 1 - Admin - New order
    state1 () {
        if (!App.caster.isAdmin) {
            throw 'L`émetteur n\'est pas un administrateur.';
        }
        
        this.setHeaderDetails();

        this.modal.querySelector('.header.free').classList.add('d-none');
        this.modal.querySelector('.description').classList.add('d-none');

        this.modal.querySelector('.online .confirm')
        .addEventListener('click', () => this.Actions.confirm());

        this.modal.querySelector('.online .pay')
        .addEventListener('click', () => this.Actions.payVADS());

        this.modal.querySelector('.actions .reserve')
        .addEventListener('click', () => this.Actions.reserve());

        // Confirm and close
        this.modal.querySelector('.actions .confirm')
        .addEventListener('click', () => this.Actions.confirmAndClose());

        // Instant payment
        this.modal.querySelector('.actions .pay')
        .addEventListener('click', () => this.Actions.payInstant());
    },

    // State 2 - Admin - Saved order
    // Hide buttons (reserve and confirm)
    state2 () {
        if (!App.caster.isAdmin) {
            throw 'L`émetteur n\'est pas un administrateur.';
        }

        if (!this.order.id) {
            throw 'Aucun numéro de reçu trouvé.';
        }

        this.reset();

        this.setHeaderDetails();

        this.modal.querySelector('.header.free').classList.add('d-none');
        this.setHeaderDetails();
        this.modal.querySelector('.description').classList.add('d-none');

        this.modal.querySelector('.online .confirm')
        .addEventListener('click', () => this.VADS.v2());

        this.modal.querySelector('.online .pay').classList.add('d-none');

        this.modal.querySelector('.actions .reserve').classList.add('d-none');
        this.modal.querySelector('.actions .confirm').classList.add('d-none');

        // Instant payment
        this.modal.querySelector('.actions .pay')
        .addEventListener('click', () => this.Actions.pay());
    },
    
    // State 3 - Parent - New order
    // Hide details
    // Hide VADS CASH CHECK
    // Hide pay action
    state3 () {
        this.setHeaderFree();

        this.modal.querySelector('.header.details').classList.add('d-none');
        this.modal.querySelector('.scrolling.content').classList.add('d-none');
        // this.modal.querySelector('.methods').classList.add('d-none');  

        this.modal.querySelector('.actions .reserve').classList.add('d-none');
        this.modal.querySelector('.actions .pay').classList.add('d-none');

        this.modal.querySelector('.actions .confirm')
        .addEventListener('click', () => this.Actions.confirm());
    },
    
    // State 4 - Parent - Saved order
    // Hide details
    // Hide VADS CASH CHECK
    state4 () {
        if (!this.order.id) {
            throw 'Aucun numéro de reçu trouvé.';
        }

        this.reset();

        this.setHeaderDetails();
        
        this.modal.querySelector('.header.free').classList.add('d-none');
        // this.modal.querySelector('.description').classList.add('d-none');
        this.modal.querySelector('.scrolling.content').classList.add('d-none');

        this.modal.querySelector('.actions .reserve').classList.add('d-none');
        this.modal.querySelector('.actions .confirm').classList.add('d-none');

        this.modal.querySelector('.actions .pay')
        .addEventListener('click', () => this.VADS.v2());
    },

    setHeaderFree () {
        this.modal.querySelector('.header.free .value').innerHTML = this.amount;
    },

    setHeaderDetails () {
        this.modal.querySelector('.amount .value').innerHTML = this.amount;

        if (this.credit) {
            this.modal.querySelector('.credit .value').innerHTML = this.credit;
        }
        else {
            this.modal.querySelector('.credit').classList.add('d-none');
        }
    },

    
    
    // payment_direct_onchange (e) { console.log(e); },
    
    message (msg) {
        const message = this.modal.querySelector('.ui.message');
        message.classList.add('show');

        if (msg.hasOwnProperty('message')) message.innerHTML = msg.message;

        else message.innerHTML = msg;
    },
    
    // Close modal
    cancel () {},
    
    // Close modal with success
    ok () {},


    Actions: {
        /**
         * 
         * @param {*} reason 
         * 
         * @reasons 
         *      Payed
         *      VADS
         *      Reserved
         *      Confirmed
         */
        close (reason) {
            $('.ui.modal').modal('hide');

            // Call summary
            // And pass reason
            console.log(reason);

            Payment.summary_cb({
                reason: reason,
                orderID: Payment.order.id
            });
        },

        cancel () {},

        async reserve () {
            await Payment.API.confirm({
                201 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.Actions.close('Payed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                402 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.VADS.v2();
                        Payment.Actions.close('Reserved');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                error (err) {
                    Payment.message(err);
                }
            });
        },

        async confirm () {
            await Payment.API.confirm({
                201 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.Actions.close('Payed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                402 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.VADS.v2();
                        Payment.Actions.close('VADS');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                error (err) {
                    Payment.message(err);
                }
            });
        },

        async confirmAndClose () {
            await Payment.API.confirm({
                201 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.Actions.close('Payed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                402 (data) {
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.Actions.close('Confirmed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                error (err) {
                    Payment.message(err);
                }
            });
        },

        async pay () {
            await Payment.API.pay(
                (res) => {
                    if (res.hasOwnProperty('order')) {
                        Payment.order.id = res.order.id;
                        Payment.Actions.close('Payed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                }
            );
        },

        async payVADS () {
            await Payment.VADS.v1();
        },

        async payInstant () {
            await Payment.API.pay_instant({
                201 (data) {
                    // console.log (data);
                    if (data.hasOwnProperty('order')) {
                        Payment.order.id = data.order.id;
                        Payment.Actions.close('Payed');
                    }
                    else {
                        Payment.message('Impossible de récupérer le numéro de reçu.');
                    }
                },
                error (err) {
                    Payment.message(err);
                }
            });
        },
    },

    Data: {
        _basePayload () {
            return {
                comment: Payment.order.comment,
        
                type: Payment.order.type,
                reference: Payment.order.reference,
        
                payer: Payment.payer.id,
                caster: Payment.order.caster,
        
                cart: Payment.cart,
            };
        },

        /**
         * Test Direct payment inputs
         */
        _methodsPayload () {            
            if (Payment.amount) {
                const cash_amount_value = Payment.direct_inputs.cash_amount.value;
                const check_amount_value = Payment.direct_inputs.check_amount.value;
                const check_ref_value = Payment.direct_inputs.check_ref.value;
        
                if (check_amount_value && !check_ref_value) {
                    throw 'Le montant et la référence chèque doivent être remplis.';
                }
        
                if (!cash_amount_value && !check_amount_value) {
                    throw 'Veuillez choisir un moyen de paiement.';
                }
        
                const methods = [];
        
                if (cash_amount_value) {
                    methods.push({
                        'method': 1, // Utils.ORDER_METHOD['CASH'],
                        'reference': '',
                        'amount': parseFloat(cash_amount_value)
                    });
                }
        
                if (check_amount_value) {
                    methods.push({
                        'method': 2, // Utils.ORDER_METHOD['CHECK'],
                        'reference': check_ref_value,
                        'amount': parseFloat(check_amount_value)
                    });
                }

                if (!methods.length) throw 'Aucune méthode de paiement valide.'

                const payload = Payment.Data._basePayload();
                payload['methods'] = methods;
                return payload;
            }
            else {
                const payload = Payment.Data._basePayload();
                return payload;
            }
        
            throw 'La commande à un montant égale à 0.'
        },
    },

    API: {

        /**
         * Macro to call the API and handle errors
         * 
         * @param {str} url 
         * @param {function} data_cb
         * @param {dict} status_cbs
         * 
         * @status_cbs {
         *      200 (data) {},
         *      201 (data) {},
         *      400 (data) {},
         *      404 (data) {},
         *      error (data, status) {},
         * }
         */
        f (url, data_cb, status_cbs) {
            try {
                const payload = data_cb();

                if (Payment.apiReady) {
                    console.log('Ready');
                    Payment.API.apiReadiness();

                    // Test purpose - Add async to function
                    // await sleep(5000);
                    // return;

                    fetch(url, {
                        method: 'POST',
                        headers: {
                            'Authorization': `Bearer ${App.token}`,
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify(payload)
                    })
                    .then(res => {
                        // console.log('THEN'); 
                        // console.log(res);
    
                        return new Promise((resolve) => {
                            res.json()
                            .then(data => 
                                resolve({
                                    status: res.status,
                                    data: data
                                })
                            )
                        });
                        
                        // if (onSuccess) onSuccess(res.json(), res.status);
                    })
                    .then(res => {
                        console.log(res);
                        
                        if (status_cbs.hasOwnProperty(res.status)) {
                            status_cbs[res.status](res.data);
                        }
                        else if (status_cbs.hasOwnProperty('error')) {
                            status_cbs.error(res.data, res.status);
                        }
                    })
                    .catch(err => {
                        // console.log('CATCH'); 
                        console.log(err);
    
                        // if (onFailure) onFailure(err);
    
                        Payment.message(err);
                    });
                }
                else {
                    console.log('Not ready');
                }
            }
            catch (e) {
                Payment.message(e);
            }
        },

        // Add methods
        // Pay an order by ID
        /**
         * 
         * @todo
         */
        async pay (onSuccess = undefined, onFailure = undefined) {
            try {
                const payload = Payment.Data._methodsPayload();

                if (Payment.apiReady) {
                    console.log('Ready');
                    Payment.API.apiReadiness();

                    // Test purpose - Add async to function
                    // await sleep(5000);
                    // return;

                    App.post(`/api/order/pay/${Payment.order.id}/`, JSON.stringify(payload.methods), true)
                    .then (res => {
                        console.log(res);
                        if (onSuccess) onSuccess(res);
                    })
                    .catch (err => {
                        console.log(err);
                        if (onFailure) onFailure(err);
                
                        if (err.hasOwnProperty('message')) Payment.message(err.message);
                        else Payment.message(err);
                    });
                }
                else {
                    console.log('Not ready');
                }
    
            }
            catch (e) {
                Payment.message(e);
            }
        },
        
        // Make an instant payment
        pay_instant (status_cbs) { // onSuccess = undefined, onFailure = undefined) {
            this.f(
                `/api/order/pay/instant/`,
                Payment.Data._methodsPayload,
                status_cbs
                // onSuccess,
                // onFailure
            );
        },
        
        // Confirm an order
        confirm (status_cbs) { // onSuccess = undefined, onFailure = undefined) {
            this.f(
                '/api/order/confirm/',
                Payment.Data._basePayload,
                status_cbs
                // onSuccess,
                // onFailure
            );
        },
        
        // Reserve an order
        reserve (status_cbs) { // onSuccess = undefined, onFailure = undefined) {
            this.f(
                '/api/order/reserve/',
                Payment.Data._basePayload,
                status_cbs
                // onSuccess,
                // onFailure
            );
        }, 

        apiReadiness () {
            Payment.apiReady = false;
            window.setTimeout(() => { Payment.apiReady = true; }, 5000);
        },
    },
    
    VADS: {
        
        v1 () {
            let link = this.vads();
            
            let formated_cart = '';
            for (const _ of Payment.cart) {
                formated_cart += `!p=${_.product},${_.children.join(',')}`;
            }
        
            link += `&lck_vads_ext_info_Informations=?v=1!pid=${Payment.payer.id}${formated_cart}`;
            
            window.open(link, '_blank');
        },
        
        v2 () {
            let link = this.vads();
        
            link += `&lck_vads_ext_info_Informations=?v=2!oid=${Payment.order.id}`;
            
            window.open(link, '_blank');
        },
        
        vads () {
            let link = Payment.VADS_BASE_LINK;
            link += `?lck_vads_amount=${Payment.amount}&lck_vads_cust_email=${Payment.payer.email}`;
        
            return link;
        },
    },
    
};

async function foo () {
    const _ = {
        url: `${App.BASE_URL}/api/order/test/`,
        method: 'POST',
        error (xhr, textStatus, errorThrown) {
            console.log(xhr);
            console.log(textStatus);
            console.log(errorThrown);
        }
    };
    
    let res = await fetch(
        `${App.BASE_URL}/api/order/test/`, 
        {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${App.token}`,
                'Content-Type': 'application/json'
            },
        })
        .then(res => {
            console.log('THEN'); console.log(res);

            return new Promise((resolve, reject) => {
                // resolve(res.json(), res.status);
                res.json()
                .then(data => {

                    resolve({
                        status: res.status,
                        data: data
                    })
                })
            });

            const data = res.text(); 
            console.log(data);
            return data;
        })
        .then ((data, status) => {
            console.log(data);
            console.log(status);
        })
        .catch(res => {console.log('CATCH'); console.log(res);})
    
    // console.log(res  .json());

    // $.ajax(_)
    // .always ((data, textStatus, jqXHR) => {
    //     console.log(data);
    //     console.log(textStatus);
    //     console.log(jqXHR);
    // })
    // .fail ((xhr, status, error) => {
    //     console.log(xhr);
    //     console.log(status);
    //     console.log(error);
    // })
}

// Old VADS function I keep there in case
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