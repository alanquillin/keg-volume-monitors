import { Component } from '@angular/core';
import { ActivatedRoute, RouterOutlet, Router, NavigationEnd } from '@angular/router';
import { filter, map, mergeMap } from 'rxjs/operators';

import { HeaderComponent } from './header/header.component';

import * as _ from 'lodash';
import { DataError, DataService } from './_services/data.service';
import {ConfigService} from './_services/config.service'
import { toBoolean } from './utils/helpers';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, HeaderComponent],
  templateUrl: './app.component.html',
  styleUrl: './app.component.scss'
})
export class AppComponent {
  title = 'Keg Volume Monitors';
  hideHeader = false;
  routeData: any;
  restricted = true;

  constructor(private dataService: DataService, private route: ActivatedRoute, private configService: ConfigService, private router: Router){}

  setConfig(data: any): void {
    console.log(data);
    this.title = _.get(data, "title", 'brewhouse-manager');
    this.hideHeader = toBoolean(_.get(data, "hideHeader", false));
    this.restricted = toBoolean(_.get(data, "access.restricted", true));
  }

  ngOnInit(): void {
    let that = this;
    this.router.events.pipe(
      filter(event => event instanceof NavigationEnd),
      map(() => this.rootRoute(this.route)),
      filter((route: ActivatedRoute) => route.outlet === 'primary'),
      mergeMap((route: ActivatedRoute) => route.data)
    ).subscribe((event: {[name: string]: any}) => {
      this.setConfig(event);

      this.dataService.unauthorized.subscribe((err: DataError) => {
        console.log(`restricted: ${this.restricted}`);
        if (this.restricted) {
          window.location.href = "/login";
        }
      })
    });
  }

  private rootRoute(route: ActivatedRoute): ActivatedRoute {
    while (route.firstChild) {
      route = route.firstChild;
    }
    return route;
  }
}
