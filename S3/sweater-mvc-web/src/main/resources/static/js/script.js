let vue = new Vue({
    el: '#app',
    data: {
        bucketName: '',
        buckets: [],
        objects: {},
        file: null
    },
    async mounted() {
        const response = await Vue.resource('buckets').get();
        const buckets = await response.json();
        this.buckets = buckets.map( b => {
            return {
                name: b.name,
                objects: []
            }
        });
        this.buckets.forEach(b => this.loadObjects(b.name));
    },
    methods: {
        async addBucket() {
            const response = await Vue.resource('buckets/add').get({name: this.bucketName});
            const bucket = await response.json();
            this.buckets.push({
                name: bucket.name,
                objects: []
            });
        },
        async deleteBucket(bucketName) {
            await Vue.resource(`buckets{/name}`).delete({name :bucketName});
            this.buckets = this.buckets.filter( bucket => {
                return bucket.name !== bucketName
            });
        },
        deleteObject(bucketName, key) {
            Vue.resource('buckets{/name}{/key}').delete({name: bucketName, key: key});
            let bucket = this.buckets.find(b => b.name == bucketName);
            bucket.objects = bucket.objects.filter(obj => obj.key != key)
        },
        async addObject(bucketName) {
            this.file = event.target.files[0];
            const response = await Vue.resource('buckets/upload').get({name: bucketName, fileName: this.file.name});
            //this.loadObjects(bucketName);
            },

        async loadObjects(bucketName) {
            const response = await Vue.resource('buckets/object-list').get({name: bucketName});
            const objectList = await response.json();
            let bucket = this.buckets.find(b => {
                return b.name == bucketName
            });
            objectList.forEach( obj => {
                bucket.objects.push(obj);
            });
        }
    }
});